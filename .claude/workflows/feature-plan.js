export const meta = {
  name: 'feature-plan',
  description: '기능 기획: 계획 작성 → 엔지니어/스켑틱 관점 검토 → 최종안 합성 (사용자 승인 전 단계)',
  whenToUse:
    'HANDOFF.md의 다음 개발 단계나 새 작업을 시작하기 전에 먼저 호출. args: {"task": "6번: 양식 업로드 + 셀 매핑 화면"} 형태로 작업 설명을 넘긴다. 결과(finalPlan)를 사용자에게 보여주고 승인받은 뒤 feature-build로 넘길 것 — 이 워크플로우는 코드를 쓰지 않는다.',
  phases: [{ title: '기획' }, { title: '검토' }, { title: '합성' }],
}

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    filesToChange: {
      type: 'array',
      items: {
        type: 'object',
        properties: { path: { type: 'string' }, change: { type: 'string' } },
        required: ['path', 'change'],
      },
    },
    steps: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          phaseName: { type: 'string' },
          actions: { type: 'array', items: { type: 'string' } },
        },
        required: ['phaseName', 'actions'],
      },
    },
    testsNeeded: { type: 'array', items: { type: 'string' } },
    risks: {
      type: 'array',
      items: {
        type: 'object',
        properties: { risk: { type: 'string' }, mitigation: { type: 'string' } },
        required: ['risk'],
      },
    },
    openQuestions: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'filesToChange', 'steps', 'testsNeeded', 'risks', 'openQuestions'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['ok', 'needs_changes'] },
    concerns: { type: 'array', items: { type: 'string' } },
    missingPieces: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'concerns', 'missingPieces'],
}

if (!args || !args.task) {
  throw new Error('args.task가 필요합니다 — 예: {"task": "6번: 양식 업로드 + 셀 매핑 화면"}')
}

phase('기획')
const planPrompt = `
다음 작업에 대한 구현 계획을 작성하라: "${args.task}"

이 저장소는 건설 일용직 노무비 관리 시스템(FastAPI 백엔드 + React/Vite 프런트엔드)이다.
계획을 쓰기 전에 반드시:
1. 저장소 루트의 CLAUDE.md와 HANDOFF.md를 읽어 현재 아키텍처·진행 상태·이미 내려진 설계 결정을 파악하라.
2. .claude/rules/ 아래 관련 규칙 파일(coding-style, python-backend-ai, javascript, databases, testing, security)을 확인하라.
3. 이 작업과 관련된 실제 기존 코드(backend/app/, frontend/src/)를 직접 읽고 기존 패턴을 그대로 따르라 — 추측하지 말 것.
4. 관련이 있다면 기획서(새 폴더/기획서/노무비_관리_시스템_기획서.md)도 참고하라.

요구사항이 모호하거나 확인이 필요한 부분은 임의로 가정하지 말고 openQuestions에 명시하라
(사용자가 이 계획을 검토한 뒤 답할 것이다 — 지금 대화하듯 묻지 말고 목록으로 남길 것).
`
const plan = await agent(planPrompt, { agentType: 'planner', schema: PLAN_SCHEMA, label: 'plan' })

phase('검토')
const [engineerReview, skepticReview] = await parallel([
  () =>
    agent(
      `아래 구현 계획을 엔지니어 관점(실현 가능성 / 누락된 부분 / 엣지케이스 / 기술적 리스크)에서 검토하라.\n\n` +
        `계획:\n${JSON.stringify(plan, null, 2)}\n\n` +
        `이 저장소의 실제 코드(backend/app/, frontend/src/)를 직접 읽어 계획이 실제 코드베이스와 어긋나지 않는지 확인하라.`,
      { agentType: 'architect', schema: REVIEW_SCHEMA, label: 'engineer-review', phase: '검토' },
    ),
  () =>
    agent(
      `아래 구현 계획을 스켑틱(회의론자) 관점에서 검토하라 — 무엇이 잘못될 수 있는가? 검증되지 않은 가정은 무엇인가?\n\n` +
        `계획:\n${JSON.stringify(plan, null, 2)}\n\n` +
        `낙관적으로 보지 말고 실패 시나리오를 적극적으로 찾아라. 이 프로젝트는 과거에 "공정은 1개로 충분하다", ` +
        `"단가는 근로자당 하나면 된다" 같은 가정이 실제 자료 확인 후 뒤집힌 전례가 있다 — 비슷한 숨은 가정이 있는지 의심하라.`,
      { schema: REVIEW_SCHEMA, label: 'skeptic-review', phase: '검토' },
    ),
])

phase('합성')
const finalPlan = await agent(
  `아래는 구현 계획과 두 관점의 검토 결과다. 이를 종합해 사용자에게 보여줄 최종 계획을 마크다운으로 작성하라.

검토에서 나온 concerns/missingPieces 중 타당한 것은 계획 내용에 반영하고, 사용자 확인이 필요한 것은
"## 확인 필요" 섹션에 명확한 질문 형태로 정리하라(계획 자체의 openQuestions도 이 섹션에 합쳐라).
두 리뷰 중 verdict가 needs_changes인 게 있으면 왜 그런지, 어떻게 반영했는지 "## 검토 반영" 섹션에 짧게 남겨라.

원본 계획: ${JSON.stringify(plan, null, 2)}
엔지니어 리뷰: ${JSON.stringify(engineerReview, null, 2)}
스켑틱 리뷰: ${JSON.stringify(skepticReview, null, 2)}
`,
  { label: 'synthesize' },
)

return { task: args.task, finalPlan, plan, engineerReview, skepticReview }
