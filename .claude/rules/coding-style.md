# 코딩 스타일

## 불변성
- 기존 객체나 컬렉션을 절대 변경하지 말 것. 새 인스턴스를 만들 것.
- Java: `List.of()`, `Map.of()`, records, `Collections.unmodifiable*` 사용.
- Python: `@dataclass(frozen=True)`, tuples, `frozenset` 사용.
- JS: spread 연산자, `Object.freeze()`, 기본은 `const` 사용.

## 파일 구조
- 작고 집중된 파일: 전형적으로 200-400줄, 최대 800줄.
- 기술 계층이 아닌 기능/도메인 중심으로 구성.
- 파일당 public 클래스/컴포넌트 1개.

## 네이밍
- 명확하게. 루프 카운터 외엔 한 글자 변수 금지.
- Java: 메서드는 `camelCase`, 클래스는 `PascalCase`, 상수는 `UPPER_SNAKE`.
- Python: 함수/변수는 `snake_case`, 클래스는 `PascalCase`.
- JS/TS: 함수/변수는 `camelCase`, 컴포넌트/클래스는 `PascalCase`.

## 함수
- 단일 책임. 함수당 최대 50줄.
- 매개변수 최대 4개. 이상이면 객체/레코드/dataclass 사용.
- 조기 반환으로 깊은 중첩 피할 것. 최대 3단계.

## 에러 처리
- 모든 레벨에서 명시적으로 처리. 예외를 무시하지 말 것.
- 사용자 대면: 친화적 메시지. 서버 측: 문맥과 함께 상세 로깅.
- 도메인별로 그룹화된 custom 예외 클래스 사용.

## 코드 품질 체크리스트
- [ ] 주석 없이 읽을 수 있는가?
- [ ] 함수 < 50줄인가?
- [ ] 파일 < 800줄인가?
- [ ] 중첩 < 4단계인가?
- [ ] 하드코딩 값이 없는가 (config/env 사용)?
- [ ] 공유 상태 변경이 없는가?
