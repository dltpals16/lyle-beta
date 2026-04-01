# BiX Beta - 난임 치료 AI 케어 컴패니언

## 실행 방법

```bash
npm install
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

## 빌드

```bash
npm run build
```

`dist/` 폴더에 정적 파일 생성 → Vercel, Netlify 등에 배포 가능

## 폴더 구조

```
bix-beta/
├── index.html              # 엔트리 HTML
├── package.json
├── vite.config.js
├── public/                  # 정적 파일
└── src/
    ├── main.jsx            # React 마운트
    ├── App.jsx             # 메인 라우팅
    ├── components/
    │   └── Layout.jsx      # 공통 컴포넌트 (Header, BottomNav, AppShell, Fade)
    ├── screens/
    │   ├── SplashScreen.jsx      # 소셜 로그인 화면
    │   ├── OnboardingScreen.jsx  # 온보딩 3단계
    │   └── MainScreens.jsx       # 홈/타임라인/AI상담/지원금/감정일기
    ├── data/
    │   └── constants.js    # 정적 데이터 (시술단계, 지역, 타임라인 등)
    └── styles/
        ├── global.css      # 글로벌 스타일
        └── theme.js        # 테마 변수 + 공통 스타일
```

## 온보딩 플로우

1. **소셜 로그인** → 카카오 / 네이버 / 구글
2. **Step 1** → 이름, 생년월일, 성별, 거주지(시/군/구)
3. **Step 2** → 시술 단계(타이밍/IUI/IVF/FET), 시술 회차
4. **Step 3** → 직전 생리 시작일

## 지원금 탭

- 첫 진입 시 혼인 여부 추가 수집
- 세액공제 전략 요청 시 맞벌이 여부, 급여구간 추가 수집
