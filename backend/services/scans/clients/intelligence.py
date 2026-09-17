import os
import httpx

from pydantic import BaseModel

class AuditResult(BaseModel):
    is_false_positive: bool
    agent_explanation: str
    suggested_explanation: str

class IntelligenceClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv('INTELLIGENCE_SERVICE_URL', 'http://127.0.0.1:8004')

    async def audit_batch(self, findings: list[dict]):
        payload = {
            'findings': [
                {
                    'file_path': f['file'],
                    'line_number': f['line_number'],
                    'category': f['category'],
                    'algorithm': f['algorithm'],
                    'matched_line': f['line_content'],
                    'code_context': f.get('code_context', '')
                }
                for f in findings
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.base_url}/intelligence/audit/batch',
                    json=payload,
                    timeout=180.0 # Generous timeout for LLM processing
                )

                if response.status_code == 200:
                    data = response.json()

                    return [AuditResult(**item) for item in data['results']]

                # If the intelligence service returned an error status:
                return [
                    AuditResult(
                        is_false_positive=False,
                        agent_explanation=f'Intelligence service error (status {response.status_code})',
                        suggested_explanation='Review manually'
                    )
                    for _ in findings
                ]

        except Exception as exc:
            # Fallback if the service is offline or timeout

            return [
                AuditResult(
                    is_false_positive=False,
                    agent_explanation=f'AI service unavailable: {str(exc)}',
                    suggested_explanation='Review manually.'
                )
                for _ in findings
            ]
