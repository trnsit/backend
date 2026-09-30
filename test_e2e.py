import asyncio
import os
from services.intelligence.agents.migration.agent import MigrationPlannerAgent
from services.intelligence.agents.migration.schemas import MigrationPlanRequest
from services.intelligence.agents.migration.executor import MigrationExecutor

async def main():
    test_dir = "temp_test_repo"
    os.makedirs(test_dir, exist_ok=True)
    test_file = "jwt_auth.py"
    file_path = os.path.join(test_dir, test_file)

    initial_code = """import jwt

def get_token(user_id, key):
    payload = {"user": user_id}
    token = jwt.encode(payload, key, algorithm="RS256")
    return token
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(initial_code)

    print("--- 1. GENERATING MIGRATION PLAN VIA AI AGENT ---")
    planner = MigrationPlannerAgent()
    request = MigrationPlanRequest(
        file_path=test_file,
        line_number=5,
        algorithm="RSA",
        category="QUANTUM_VULNERABLE",
        code_content=initial_code
    )

    plan = await planner.plan_migration(request)
    print(f"Complexity: {plan.complexity}")
    print(f"Explanation: {plan.explanation}")
    print(f"Library Required: {plan.library_required}")

    print("\n--- 2. EXECUTING MIGRATION (WITH SYNTAX VALIDATION) ---")
    result = MigrationExecutor.apply_migration(
        repo_path=test_dir,
        file_rel_path=test_file,
        migrated_file_content=plan.migrated_file_content
    )
    print("Execution Result:", result)

    print("\n--- 3. MODIFIED FILE CONTENT ON DISK ---")
    with open(file_path, "r", encoding="utf-8") as f:
        print(f.read())

    # Clean up test files
    os.remove(file_path)
    os.rmdir(test_dir)

if __name__ == "__main__":
    asyncio.run(main())
