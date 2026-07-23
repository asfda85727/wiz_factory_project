# JavaScript — Express.js & React

## 일반 JS 표준
- 기본은 `const`, 재할당 필요 시 `let`. `var` 금지.
- 콜백과 인라인 함수는 화살표 함수.
- 사용 지점에서 객체와 배열 destructure.
- 문자열 연결 대신 template literal 사용.
- `.then()` 체인 대신 `async/await` 사용.

## Express.js API 규칙
- 라우트는 도메인별로 구성: `routes/users.js`, `routes/orders.js`.
- 중앙 error-handling 미들웨어 사용. unhandled rejection으로 서버 크래시 금지.
- 요청 본문 검증은 `joi`, `zod`, 또는 `express-validator`.
- 보안 헤더는 `helmet`, CORS는 `cors`.
- 환경 설정은 `dotenv`. 전역적으로 `process.env` 접근하지 말고 config 모듈로.
- HTTP 상태 코드 올바르게 사용: 200 성공, 201 생성, 400 잘못된 입력, 401 미인증, 404 찾을 수 없음, 500 서버 오류.

## Express 프로젝트 구조
```
src/
  app.js            # Express 앱 설정, 미들웨어
  server.js         # 서버 시작
  routes/           # 라우트 핸들러
  controllers/      # 요청 처리 로직
  services/         # 비즈니스 로직
  models/           # DB 모델/스키마
  middleware/       # 인증, 검증, 에러 처리
  config/           # 환경, DB 연결
```

## React 규칙
- 함수형 컴포넌트만. 클래스 컴포넌트 금지.
- Hooks 사용: `useState`, `useEffect`, `useContext`, `useMemo`, `useCallback`.
- 재사용 로직은 custom hook. `use`로 시작.
- 컴포넌트는 작고 집중. 약 150줄 넘으면 분리.
- Props: 함수 시그니처에서 destructure. 적절히 기본값 설정.
- 상태 관리: 단순 상태는 React Context. 복잡한 상태는 Zustand 또는 Redux Toolkit 고려.
- API는 `fetch` 또는 `axios`로 중앙 집중식 API client 사용. 컴포넌트에서 직접 호출 금지.

## React 프로젝트 구조
```
src/
  components/       # 재사용 UI 컴포넌트
  pages/            # 라우트 단위 컴포넌트
  hooks/            # Custom hooks
  context/          # React context 제공자
  services/         # API client와 호출
  utils/            # 헬퍼 함수
```

## 피해야 할 흔한 실수
- 프로덕션 코드에 `console.log` 금지. logger 사용하거나 커밋 전 제거.
- TypeScript 사용 시 `any` 금지. 타입 없는 API 응답 금지.
- React에서 직접 DOM 조작 금지. ref는 필요할 때만.
- 인라인 스타일은 일회성 동적 값만. 나머지는 클래스/css-in-js.
- 라우트 핸들러(Express) 또는 컴포넌트(React)에 비즈니스 로직 금지. 서비스로 위임.
