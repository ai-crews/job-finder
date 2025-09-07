import json
import os
import logging
from datetime import datetime
from services.email_sender import send_personalized_email
from services.job_matcher import get_personalized_jobs
from db.db_aws import Database
from db.db_query import EmailQueries

# Lambda용 로거 설정 (CloudWatch Logs 사용)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """AWS Lambda 핸들러 함수 - 매주 목요일 오전 11시 실행"""
    logger.info("=== Lambda 개인화된 채용공고 이메일 발송 시작 ===")

    start_time = datetime.now()
    success_count = 0
    fail_count = 0
    total_users = 0

    try:
        # Lambda 실행 정보 로깅
        logger.info(
            f"Lambda 함수명: {context.function_name if context else 'local_test'}"
        )
        logger.info(f"요청 ID: {context.aws_request_id if context else 'local_test'}")
        logger.info(f"실행 시작 시간: {start_time}")

        # DB에서 구독자 조회
        with Database.get_cursor() as (cursor, connection):
            cursor.execute(EmailQueries.GET_ACTIVE_SUBSCRIBERS)
            users = cursor.fetchall()
            total_users = len(users)

            if not users:
                logger.warning("구독 중인 사용자가 없습니다.")
                return {
                    "statusCode": 200,
                    "body": json.dumps(
                        {
                            "message": "구독 중인 사용자가 없습니다.",
                            "total_users": 0,
                            "success": 0,
                            "failed": 0,
                            "execution_time_seconds": 0,
                        },
                        ensure_ascii=False,
                    ),
                }

            logger.info(f"발송 대상: {total_users}명")

        # 각 사용자별로 개인화된 이메일 발송
        for idx, user in enumerate(users):
            user_id, email, name = user[0], user[1], user[2]
            logger.info(f"사용자 처리 중 ({idx+1}/{total_users}): {name}({email})")

            try:
                # 개인화된 채용공고 가져오기
                recommended_jobs = get_personalized_jobs(email, top_n=10)

                if recommended_jobs:
                    logger.info(f"추천 공고 {len(recommended_jobs)}개 발견 - {email}")

                    # 개인화된 이메일 발송
                    results = send_personalized_email(email, name, recommended_jobs)

                    # 발송 결과 로그 기록
                    with Database.get_cursor() as (cursor, connection):
                        status = (
                            "SUCCESS" if results[email][0] == "SUCCESS" else "FAILED"
                        )
                        error_msg = results[email][1] if status == "FAILED" else None

                        cursor.execute(
                            EmailQueries.INSERT_EMAIL_LOG,
                            (
                                user_id,
                                email,
                                f"{name}님을 위한 맞춤 채용공고",
                                "PERSONALIZED",
                                status,
                                error_msg,
                                len(recommended_jobs),
                            ),
                        )
                        connection.commit()

                        if status == "SUCCESS":
                            success_count += 1
                            logger.info(f"✅ 이메일 발송 성공: {email}")
                        else:
                            fail_count += 1
                            logger.error(f"❌ 이메일 발송 실패: {email} - {error_msg}")

                else:
                    logger.warning(f"추천할 공고가 없습니다: {email}")
                    # 추천 공고 없는 경우도 로그 기록
                    with Database.get_cursor() as (cursor, connection):
                        cursor.execute(
                            EmailQueries.INSERT_EMAIL_LOG,
                            (
                                user_id,
                                email,
                                "추천 공고 없음",
                                "PERSONALIZED",
                                "FAILED",
                                "추천할 공고가 없습니다",
                                0,
                            ),
                        )
                        connection.commit()
                    fail_count += 1

            except Exception as user_error:
                fail_count += 1
                logger.error(f"사용자 {email} 처리 중 오류: {user_error}")

                # 에러 로그 기록
                try:
                    with Database.get_cursor() as (cursor, connection):
                        cursor.execute(
                            EmailQueries.INSERT_EMAIL_LOG,
                            (
                                user_id,
                                email,
                                "처리 오류",
                                "PERSONALIZED",
                                "FAILED",
                                str(user_error),
                                0,
                            ),
                        )
                        connection.commit()
                except Exception as log_error:
                    logger.error(f"에러 로그 기록 실패: {log_error}")

        # 실행 시간 계산
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 성공률 계산
        success_rate = (success_count / total_users * 100) if total_users > 0 else 0

        # 최종 결과 로깅
        logger.info("=== Lambda 실행 완료 ===")
        logger.info(f"총 사용자: {total_users}명")
        logger.info(f"발송 성공: {success_count}건")
        logger.info(f"발송 실패: {fail_count}건")
        logger.info(f"성공률: {success_rate:.1f}%")
        logger.info(f"총 실행 시간: {execution_time:.2f}초")

        # Lambda 응답 반환
        result = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "이메일 발송 완료",
                    "total_users": total_users,
                    "success": success_count,
                    "failed": fail_count,
                    "success_rate": round(success_rate, 1),
                    "execution_time_seconds": round(execution_time, 2),
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "remaining_time_ms": (
                        context.get_remaining_time_in_millis() if context else None
                    ),
                },
                ensure_ascii=False,
            ),
        }

        return result

    except Exception as e:
        # 치명적 오류 처리
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        logger.critical(f"Lambda 실행 중 치명적 오류: {e}")
        logger.error(f"실행 시간: {execution_time:.2f}초")

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "total_users": total_users,
                    "success": success_count,
                    "failed": fail_count,
                    "execution_time_seconds": round(execution_time, 2),
                    "timestamp": datetime.now().isoformat(),
                },
                ensure_ascii=False,
            ),
        }
