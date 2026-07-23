export const meta = {
  name: 'feature-build',
  description: '승인된 계획 구현 → 코드/보안 리뷰 → 보완 → 검증(pytest/build), 실패 시 재보완',
  whenToUse:
    'feature-plan이 만든 계획을 사용자가 승인한 뒤 호출. args: {"task": "...", "plan": "<feature-plan 결과의 finalPlan 텍스트>"}. 이 프로젝트는 아직 git 미초기화 상태라 리뷰 단계는 git diff 대신 구현 단계가 보고한 파일 목록을 직접 Read한다.',
  phases: [{ title: '구현' }, { title: '리뷰' }, { title: '보완' }, { title: '검증' }],
}

const IMPLEMENT_SCHEMA = {
  type: 'object',
  properties: {
    filesChanged: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    sidesTouched: { type: 'array', items: { type: 'string', enum: ['backend', 'frontend'] } },
  },
  required: ['filesChanged', 'summary', 'sidesTouched'],
}

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['CRITICAL', 'WARNING', 'SUGGESTION'] },
          file: { type: 'string' },
          line: { type: 'number' },
          summary: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['severity', 'file', 'summary', 'fix'],
      },
    },
  },
  required: ['findings'],
}

const FIX_SCHEMA = {
  type: 'object',
  properties: {
    fixed: { type: 'array', items: { type: 'string' } },
    skipped: {
      type: 'array',
      items: {
        type: 'object',
        properties: { summary: { type: 'string' }, reason: { type: 'string' } },
        required: ['summary', 'reason'],
      },
    },
  },
  required: ['fixed', 'skipped'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    passed: { type: 'boolean' },
    backend: {
      type: 'object',
      properties: { ran: { type: 'boolean' }, passed: { type: 'boolean' }, output: { type: 'string' } },
    },
    frontend: {
      type: 'object',
      properties: { ran: { type: 'boolean' }, passed: { type: 'boolean' }, output: { type: 'string' } },
    },
  },
  required: ['passed'],
}

if (!args || !args.task || !args.plan) {
  throw new Error('args.task, args.plan이 필요합니다 (feature-plan 결과의 finalPlan을 그대로 전달할 것)')
}

phase('구현')
const implementation = await agent(
  `아래 승인된 계획대로 구현하라: "${args.task}"

계획(사용자 승인됨):
${args.plan}

규칙:
- 저장소 루트의 CLAUDE.md와 .claude/rules/의 관련 규칙(coding-style, python-backend-ai, javascript, databases, testing, security)을 반드시 따를 것.
- testing.md 원칙대로 TDD로 진행하라: 실패하는 테스트를 먼저 쓰고(RED) → 최소 구현으로 통과시키고(GREEN) → 리팩터링(IMPROVE).
- 기존 코드 패턴(레이어 구조 routers→services→repositories→models, RFC7807 도메인 예외, 커서 페이지네이션 등)을 그대로 따르고 새 스타일을 만들지 말 것.
- 완료 후 관련된 백엔드 pytest / 프런트엔드 tsc -b를 최소 1회 실행해 구문 오류가 없는지 스스로 확인하라(전체 검증은 다음 단계에서 별도로 한다).
- 실제로 만들거나 수정한 파일의 정확한 저장소 기준 상대경로 목록을 빠짐없이 보고하라.`,
  { schema: IMPLEMENT_SCHEMA, label: 'implement' },
)

phase('리뷰')
const fileList = implementation.filesChanged.join('\n')
const [codeReview, securityReview] = await parallel([
  () =>
    agent(
      `다음 파일들이 이번 작업으로 변경/생성되었다(이 저장소는 git 미초기화 상태이므로 git diff 대신 아래 경로를 각각 Read로 직접 읽어 리뷰하라):\n${fileList}\n\n` +
        `작업 배경: ${args.task}\n\n각 파일을 전체 읽고 체크리스트대로 리뷰하라.`,
      { agentType: 'code-reviewer', schema: FINDINGS_SCHEMA, label: 'code-review', phase: '리뷰' },
    ),
  () =>
    agent(
      `다음 파일들이 이번 작업으로 변경/생성되었다(git 미초기화 상태이므로 git diff 대신 아래 경로를 직접 Read로 읽어 스캔하라):\n${fileList}\n\n` +
        `작업 배경: ${args.task}\n\n각 파일을 읽고 보안 체크리스트대로 스캔하라. 이 프로젝트는 근로자 PII(주민등록번호/계좌번호)를 다루므로 ` +
        `암호화·마스킹·인증 누락에 특히 주의하라.`,
      { agentType: 'security-reviewer', schema: FINDINGS_SCHEMA, label: 'security-review', phase: '리뷰' },
    ),
])

const allFindings = [...codeReview.findings, ...securityReview.findings]
const actionable = allFindings.filter((f) => f.severity !== 'SUGGESTION')

phase('보완')
let fixResult = { fixed: [], skipped: [] }
if (actionable.length > 0) {
  fixResult = await agent(
    `아래 리뷰 findings 중 CRITICAL/WARNING 항목을 수정하라. SUGGESTION 수준은 건드리지 않아도 된다.

findings:
${JSON.stringify(actionable, null, 2)}

각 항목에 대해 실제로 고쳤으면 fixed 목록에 무엇을 어떻게 고쳤는지 적고, 고치지 않기로 했으면(예: 오탐,
이 프로젝트의 기존 결정과 충돌 등) skipped에 이유와 함께 남겨라.`,
    { schema: FIX_SCHEMA, label: 'fix', phase: '보완' },
  )
}

phase('검증')
async function runVerify(label) {
  return agent(
    `다음을 Bash로 실제 실행해 검증하라(결과를 절대 지어내지 말 것 — 반드시 실행할 것):
${implementation.sidesTouched.includes('backend') ? '- 백엔드: cd backend && ./.venv/Scripts/python.exe -m pytest tests/ -v\n' : ''}${implementation.sidesTouched.includes('frontend') ? '- 프런트엔드: cd frontend && npm run build && npm run lint\n' : ''}
각 실행의 pass/fail 여부와, 실패 시 에러 메시지 전문을 그대로 보고하라.`,
    { schema: VERIFY_SCHEMA, label, phase: '검증' },
  )
}

let verification = await runVerify('verify')
let retries = 0
while (!verification.passed && retries < 2) {
  retries += 1
  log(`검증 실패 (${retries}차 재시도) — 실패 로그 기반으로 보완 진행`)
  const retryFix = await agent(
    `검증 실행 결과 실패했다. 아래 출력을 보고 원인을 진단해 고쳐라:
백엔드: ${verification.backend ? verification.backend.output : '(실행 안 함)'}
프런트엔드: ${verification.frontend ? verification.frontend.output : '(실행 안 함)'}`,
    { schema: FIX_SCHEMA, label: `retry-fix-${retries}`, phase: '보완' },
  )
  fixResult.fixed.push(...retryFix.fixed)
  fixResult.skipped.push(...retryFix.skipped)
  verification = await runVerify(`verify-${retries}`)
}

return {
  task: args.task,
  filesChanged: implementation.filesChanged,
  implementationSummary: implementation.summary,
  reviewFindings: allFindings,
  fixesApplied: fixResult,
  verification,
  retries,
}
