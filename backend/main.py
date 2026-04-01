"""
라일(Lyle) 챗봇 — 로컬 테스트 스크립트
터미널에서 대화형으로 테스트합니다.
"""
from datetime import date
from models import UserProfile, Gender
from core.orchestrator import LyleChatbot


def main():
    print("\n" + "=" * 60)
    print("  💜 라일(Lyle) AI 챗봇 — 로컬 테스트 모드")
    print("=" * 60)

    # 챗봇 초기화
    bot = LyleChatbot()

    # 테스트 유저 등록
    test_user = UserProfile(
        user_id="test_001",
        name="테스트",
        birth_date=date(1990, 5, 15),
        gender=Gender.FEMALE,
        last_period_date=date(2025, 2, 1),
        treatment_stage="체외수정",
        treatment_cycle=2,
        protocol="장기요법",
        current_phase="이식 후 D+7",
        region="서울",
    )
    print(bot.register_user(test_user))
    print(f"\n유저 프로필:\n{test_user.context_summary()}")
    print("-" * 60)

    # 대화 루프
    print("\n대화를 시작합니다. 종료하려면 'quit' 또는 'q'를 입력하세요.\n")

    while True:
        user_input = input("\n👤 나: ").strip()

        if user_input.lower() in ("quit", "q", "exit"):
            print("\n💜 대화를 종료합니다. 언제든 다시 찾아오세요!")
            break

        if not user_input:
            continue

        # 특수 명령어
        if user_input == "/profile":
            profile = bot.get_profile("test_001")
            print(f"\n📋 현재 프로필:\n{profile.context_summary()}")
            continue

        if user_input == "/reset":
            bot.reset_session("test_001")
            print("\n🔄 세션이 초기화되었습니다.")
            continue

        if user_input == "/help":
            print("\n📌 명령어:")
            print("  /profile — 현재 프로필 확인")
            print("  /reset — 대화 세션 초기화")
            print("  /help — 도움말")
            print("  quit — 종료")
            continue

        # 파이프라인 실행
        print()
        result = bot.chat("test_001", user_input)

        # 응답 출력
        print(f"\n💜 라일: {result.response}")

        if result.safety_flags:
            print(f"\n⚠️ 안전 플래그: {result.safety_flags}")

        if result.profile_updates:
            print(f"\n📝 프로필 업데이트: {result.profile_updates}")


if __name__ == "__main__":
    main()
