import concurrent.futures
import time
from datetime import datetime
from app import app
from app.models import db, Token
from app.routes.user import generate_service_token

NUM_CONCURRENT_USERS = 30
SERVICE_TO_TEST = "Deposit"

def simulate_user_request(simulated_user_id):
    """
    Simulates a concurrent customer request under load.
    """
    with app.app_context():
        try:
            token_num = generate_service_token(SERVICE_TO_TEST)
            token = Token(
                token_number=token_num,
                service_type=SERVICE_TO_TEST,
                priority=2,
                status="waiting",
                user_id=simulated_user_id,
                created_at=datetime.now()
            )
            db.session.add(token)
            db.session.commit()
            return {"status": "SUCCESS", "token": token_num, "user_id": simulated_user_id}
        except Exception as e:
            db.session.rollback()
            return {"status": "ERROR", "error": str(e), "user_id": simulated_user_id}

def run_stress_test():
    print("=" * 60)
    print("CONCURRENCY BENCHMARK TEST")
    print(f"Workers: {NUM_CONCURRENT_USERS} parallel threads")
    print(f"Target Service: {SERVICE_TO_TEST}")
    print("=" * 60)

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CONCURRENT_USERS) as executor:
        user_ids = list(range(200, 200 + NUM_CONCURRENT_USERS))
        results = list(executor.map(simulate_user_request, user_ids))

    total_time = round(time.time() - start_time, 3)

    successful_tokens = [r["token"] for r in results if r["status"] == "SUCCESS"]
    failed_requests = [r for r in results if r["status"] == "ERROR"]
    unique_tokens = set(successful_tokens)
    duplicates = [t for t in successful_tokens if successful_tokens.count(t) > 1]

    print("\nBenchmark Results:")
    print(f"Total Execution Time: {total_time}s")
    print(f"Throughput: {round(NUM_CONCURRENT_USERS / total_time, 1)} req/sec")
    print(f"Successful Requests: {len(successful_tokens)} / {NUM_CONCURRENT_USERS}")
    print(f"Failed Requests: {len(failed_requests)}")
    print(f"Unique Tokens: {len(unique_tokens)}")

    print("\nIntegrity Verification:")
    if len(duplicates) == 0 and len(successful_tokens) == NUM_CONCURRENT_USERS:
        print("PASSED: 0 duplicates detected. Race conditions mitigated successfully.")
        print(f"Generated Range: {successful_tokens[0]} -> {successful_tokens[-1]}")
    else:
        print(f"FAILED: Duplicate tokens detected: {set(duplicates)}")

    print("=" * 60)

if __name__ == "__main__":
    run_stress_test()