import { useState, useEffect } from 'react';
import { AppShell, TopNav } from './components/Layout';
import SplashScreen from './screens/SplashScreen';
import OnboardingScreen from './screens/OnboardingScreen';
import { HomeScreen, TimelineScreen, ChatScreen, CalcScreen, RecordsScreen, MyPageScreen } from './screens/MedicalScreens';
import { HomeScreen as NatHomeScreen, ChatScreen as NatChatScreen, RecordsScreen as NatRecordsScreen, CalcScreen as NatCalcScreen, MyPageScreen as NatMyPageScreen } from './screens/NaturalScreens';
import { logOut, saveUserProfile, getUserProfile, deleteAccount, getSavedNickname, saveNickname } from './auth/firebase';

const generateGuestId = () => 'guest_' + Math.random().toString(36).slice(2, 10);

export default function App() {
  const [loading, setLoading] = useState(true);
  const [screen, setScreen] = useState('main');
  const [tab, setTabRaw] = useState(() => sessionStorage.getItem('lyle_tab') || 'home');
  const setTab = (t) => { sessionStorage.setItem('lyle_tab', t); setTabRaw(t); };
  const [splashInitialView, setSplashInitialView] = useState(null);
  const [pendingChatMessage, setPendingChatMessage] = useState(null);
  const [uid, setUid] = useState(null);
  const [user, setUser] = useState(null);

  // 저장된 닉네임으로 자동 로그인, 없으면 게스트로 시작
  useEffect(() => {
    const loadUser = async () => {
      const nickname = getSavedNickname();
      if (nickname) {
        try {
          const profile = await getUserProfile(nickname);
          if (profile && profile.onboardingComplete) {
            setUid(nickname);
            setUser({
              name: profile.displayName || nickname,
              mode: profile.mode || 'natural',
              birthYear: profile.birthYear,
              gender: profile.gender,
              region1: profile.region1,
              region2: profile.region2,
              stage: profile.stage,
              ivfPhase: profile.ivfPhase || '',
              cycle: profile.cycle,
              totalFrozenEmbryos: profile.totalFrozenEmbryos ?? null,
              protocol: profile.protocol || '',
              infertilityDuration: profile.infertilityDuration || '',
              amh: profile.amh || '',
              diagnoses: profile.diagnoses || [],
              periodDate: profile.periodDate,
              marriageStatus: profile.marriageStatus || null,
              currentPhase: profile.current_phase || '',
              notificationSettings: profile.notification_settings || {},
              phone: profile.phone || '',
              hospital: profile.hospital || '',
            });
            setScreen('main');
            if (!sessionStorage.getItem('lyle_tab')) setTab('home');
          } else if (profile) {
            setUid(nickname);
            setScreen('onboarding');
          } else {
            // 프로필 없음 = 삭제된 계정 → 게스트로
            const guestId = generateGuestId();
            setUid(guestId);
            setUser({ name: '게스트', isGuest: true });
            setScreen('main');
            setTab('chat');
          }
        } catch {
          const guestId = generateGuestId();
          setUid(guestId);
          setUser({ name: '게스트', isGuest: true });
          setScreen('main');
          setTab('chat');
        }
      } else {
        // 처음 방문 → 온보딩 (모드 선택부터)
        setScreen('onboarding');
      }
      setLoading(false);
    };
    loadUser();
  }, []);

  // 닉네임 인증 완료 핸들러
  const handleAuth = async (authUser) => {
    setUid(authUser.uid);
    // 새 사용자는 Firebase 등록 없이 바로 온보딩
    if (authUser.isNewUser) {
      setScreen('onboarding');
      return;
    }
    const profile = await getUserProfile(authUser.uid);
    if (profile && profile.onboardingComplete) {
      setUser({
        name: profile.displayName || authUser.displayName || '',
        mode: profile.mode || 'natural',
        birthYear: profile.birthYear,
        gender: profile.gender,
        region1: profile.region1,
        region2: profile.region2,
        stage: profile.stage,
        ivfPhase: profile.ivfPhase || '',
        cycle: profile.cycle,
        totalFrozenEmbryos: profile.totalFrozenEmbryos ?? null,
        protocol: profile.protocol || '',
        infertilityDuration: profile.infertilityDuration || '',
        amh: profile.amh || '',
        diagnoses: profile.diagnoses || [],
        periodDate: profile.periodDate,
        marriageStatus: profile.marriageStatus || null,
        currentPhase: profile.current_phase || '',
        notificationSettings: profile.notification_settings || {},
        phone: profile.phone || '',
        hospital: profile.hospital || '',
      });
      setScreen('main');
    } else {
      setScreen('onboarding');
    }
  };

  const handleOnboardingComplete = async (form) => {
    // 새 온보딩: mode, periodDate, cycle, procedure, protocol, stage, phone, nickname, consent
    const nickname = form.nickname?.trim() || uid;
    const userData = {
      displayName: nickname,
      mode: form.mode || 'natural',
      periodDate: form.periodDate || '',
      cycle: form.cycle || '',
      stage: form.procedure || form.mode || 'natural', // procedure가 있으면 시술 종류, 없으면 mode
      ivfPhase: form.stage || '', // IVF/IUI 세부 단계
      protocol: form.protocol || '',
      phone: form.phone || '',
      consentNotification: form.consent?.notification || false,
    };

    // 닉네임을 uid로 사용
    const finalUid = nickname;
    setUid(finalUid);

    try {
      await saveUserProfile(finalUid, userData);
      saveNickname(finalUid);
    } catch (e) {
      console.error('프로필 저장 오류:', e);
      alert('저장 중 오류가 발생했습니다. 다시 시도해주세요.');
      return;
    }

    setUser({
      name: nickname,
      mode: userData.mode,
      periodDate: userData.periodDate,
      cycle: userData.cycle,
      stage: userData.stage,
      ivfPhase: userData.ivfPhase,
      protocol: userData.protocol,
      phone: userData.phone,
    });
    setScreen('main');
    setTab('chat');
  };

  const handleProfileUpdate = async (updatedForm) => {
    const userData = {
      displayName: updatedForm.name,
      stage: updatedForm.stage,
      ivfPhase: updatedForm.ivfPhase || '',
      cycle: updatedForm.cycle,
      totalFrozenEmbryos: updatedForm.totalFrozenEmbryos ?? null,
      protocol: updatedForm.protocol || '',
      periodDate: updatedForm.periodDate,
      region1: updatedForm.region1,
      region2: updatedForm.region2,
      infertilityDuration: updatedForm.infertilityDuration || '',
      amh: updatedForm.amh || '',
      diagnoses: updatedForm.diagnoses || [],
      marriageStatus: updatedForm.marriageStatus || '',
    };
    await saveUserProfile(uid, userData);
    setUser(prev => ({
      ...prev,
      name: updatedForm.name,
      stage: updatedForm.stage,
      ivfPhase: updatedForm.ivfPhase || '',
      cycle: updatedForm.cycle,
      totalFrozenEmbryos: updatedForm.totalFrozenEmbryos ?? null,
      protocol: updatedForm.protocol || '',
      periodDate: updatedForm.periodDate,
      region1: updatedForm.region1,
      region2: updatedForm.region2,
      infertilityDuration: updatedForm.infertilityDuration || '',
      amh: updatedForm.amh || '',
      diagnoses: updatedForm.diagnoses || [],
      marriageStatus: updatedForm.marriageStatus || '',
    }));
  };

  const handleLogout = async () => {
    await logOut();
    const guestId = generateGuestId();
    setUid(guestId);
    setUser({ name: '게스트', isGuest: true });
    setScreen('main');
    setTab('chat');
  };

  const handleDeleteAccount = async () => {
    try {
      await deleteAccount();
      const guestId = generateGuestId();
      setUid(guestId);
      setUser({ name: '게스트', isGuest: true });
      setScreen('main');
      setTab('chat');
    } catch (e) {
      alert('탈퇴 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
      throw e;
    }
  };

  const handleRegister = () => {
    setScreen('splash');
  };
  const handleLogin = () => {
    setSplashInitialView('login');
    setScreen('splash');
  };

  // 초기 로딩
  if (loading) {
    return (
      <AppShell>
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          minHeight: '100vh',
        }}>
          <div style={{ textAlign: 'center', color: '#8C839E' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🌱</div>
            <div style={{ fontSize: 14 }}>로딩 중...</div>
          </div>
        </div>
      </AppShell>
    );
  }

  if (screen === 'splash') {
    return (
      <AppShell>
        <SplashScreen onAuth={handleAuth} initialView={splashInitialView} onBack={() => {
          setSplashInitialView(null);
          const guestId = generateGuestId();
          setUid(guestId);
          setUser({ name: '게스트', isGuest: true });
          setScreen('main');
          setTab('chat');
        }} />
      </AppShell>
    );
  }

  if (screen === 'onboarding') {
    return (
      <AppShell>
        <OnboardingScreen
          onComplete={handleOnboardingComplete}
          defaultName={uid || ''}
          onCancel={() => {
            setScreen('splash');
            setUid(null);
            setUser(null);
          }}
          onGuest={(mode) => {
            const guestId = generateGuestId();
            setUid(guestId);
            setUser({ name: '게스트', isGuest: true, mode: mode || 'medical' });
            setScreen('main');
            if (!sessionStorage.getItem('lyle_tab')) setTab('home');
          }}
          onLogin={() => {
            setSplashInitialView('login');
            setScreen('splash');
          }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell mode={user?.mode}>
      <TopNav active={tab} setTab={setTab}
        userName={user?.name || uid || ''}
        userEmail={uid || ''}
        onLogout={handleLogout}
        mode={user?.mode}
        isGuest={user?.isGuest}
      />
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {(() => {
          const isNat = user?.mode === 'natural';
          const Home = isNat ? NatHomeScreen : HomeScreen;
          const Chat = isNat ? NatChatScreen : ChatScreen;
          const Records = isNat ? NatRecordsScreen : RecordsScreen;
          const Calc = isNat ? NatCalcScreen : CalcScreen;
          const MyPage = isNat ? NatMyPageScreen : MyPageScreen;
          return (
            <>
              {tab === 'home' && <Home setTab={setTab} user={user} uid={uid} setUser={setUser} onCheckQuestion={(msg) => { setPendingChatMessage(msg); setTab('chat'); }} onStartOnboarding={() => { setScreen('onboarding'); setUid(null); setUser(null); }} />}
              {tab === 'timeline' && <TimelineScreen user={user} uid={uid} setUser={setUser} />}
              {tab === 'chat' && <Chat user={user} uid={uid} pendingMessage={pendingChatMessage} onPendingConsumed={() => setPendingChatMessage(null)} setUser={setUser} />}
              {tab === 'records' && <Records user={user} uid={uid} setUser={setUser} onStartOnboarding={() => { setScreen('onboarding'); setUid(null); setUser(null); }} />}
              {tab === 'calc' && <Calc user={user} uid={uid} setUser={setUser} setTab={setTab} onStartOnboarding={() => { setScreen('onboarding'); setUid(null); setUser(null); }} />}
              {tab === 'mypage' && <MyPage user={user} uid={uid} onSave={handleProfileUpdate} onLogout={handleLogout} onDeleteAccount={handleDeleteAccount} onRegister={handleRegister} onLogin={handleLogin} email={uid || ''} setUser={setUser} onStartOnboarding={() => { setScreen('onboarding'); }} />}
            </>
          );
        })()}
      </div>
    </AppShell>
  );
}
