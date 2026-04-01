import { useState, useEffect } from 'react';
import { theme, btnPrimary, inputStyle, labelStyle } from '../styles/theme';
import { Fade } from '../components/Layout';
import { registerWithNickname, loginWithNickname, checkNickname } from '../auth/firebase';

export default function SplashScreen({ onAuth, initialView }) {
  const [show, setShow] = useState(false);
  const [mode, setMode] = useState(initialView || 'splash'); // 'splash' | 'register' | 'login'
  useEffect(() => { if (initialView) setMode(initialView); }, [initialView]);
  const [nickname, setNickname] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [checking, setChecking] = useState(false);
  const [nicknameAvailable, setNicknameAvailable] = useState(null); // null | true | false
  useEffect(() => { setTimeout(() => setShow(true), 100); }, []);

  // 닉네임 중복 체크 (디바운스)
  useEffect(() => {
    if (mode !== 'register' || nickname.trim().length < 2) {
      setNicknameAvailable(null);
      return;
    }
    setChecking(true);
    const timer = setTimeout(async () => {
      try {
        const exists = await checkNickname(nickname.trim());
        setNicknameAvailable(!exists);
      } catch {
        setNicknameAvailable(null);
      }
      setChecking(false);
    }, 500);
    return () => clearTimeout(timer);
  }, [nickname, mode]);

  const handleRegister = async (e) => {
    e.preventDefault();
    const trimmed = nickname.trim();
    if (trimmed.length < 2) { setError('닉네임은 2자 이상이어야 해요.'); return; }
    if (trimmed.length > 12) { setError('닉네임은 12자 이하로 입력해주세요.'); return; }
    setLoading(true);
    setError(null);
    try {
      // 중복 체크만 하고, 실제 등록은 온보딩 완료 시 수행
      const exists = await checkNickname(trimmed);
      if (exists) {
        setError('이미 사용 중인 닉네임이에요.');
        setLoading(false);
        return;
      }
      onAuth({ uid: trimmed, displayName: trimmed, isNewUser: true });
    } catch (err) {
      setError('오류가 발생했어요. 다시 시도해주세요.');
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const trimmed = nickname.trim();
    if (!trimmed) { setError('닉네임을 입력해주세요.'); return; }
    setLoading(true);
    setError(null);
    try {
      const user = await loginWithNickname(trimmed);
      onAuth(user);
    } catch (err) {
      if (err.code === 'nickname/not-found') setError('등록되지 않은 닉네임이에요.');
      else setError('오류가 발생했어요. 다시 시도해주세요.');
      setLoading(false);
    }
  };

  // 스플래시 화면
  if (mode === 'splash') {
    return (
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        background: `linear-gradient(165deg, ${theme.primaryBg} 0%, #EEEAFF 60%, ${theme.primaryLight} 100%)`,
        padding: 40, minHeight: '100vh',
      }}>
        <Fade show={show}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              width: 84, height: 84, borderRadius: 22,
              background: `linear-gradient(135deg, ${theme.primary}, ${theme.accent})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 28px', fontSize: 38,
              boxShadow: '0 10px 36px rgba(124,106,175,0.3)',
            }}>🌱</div>
            <div style={{
              fontSize: 36, fontWeight: 800, color: theme.text,
              letterSpacing: -1, marginBottom: 12,
            }}>Lyle</div>
            <div style={{
              fontSize: 17, color: theme.textSub, lineHeight: 1.7, marginBottom: 52,
            }}>
              난임 치료 여정을 함께하는 AI 케어 컴패니언
            </div>
          </div>
        </Fade>

        <Fade show={show} delay={300}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: 360 }}>
            <button onClick={() => { setMode('register'); setNickname(''); setError(null); }} style={{
              ...btnPrimary,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}>
              시작하기
            </button>
            <button onClick={() => { setMode('login'); setNickname(''); setError(null); }} style={{
              ...btnPrimary, background: theme.card, color: theme.text,
              border: `1.5px solid ${theme.border}`,
              boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}>
              기존 닉네임으로 로그인
            </button>
          </div>
        </Fade>

        <Fade show={show} delay={500}>
          <p style={{ fontSize: 11, color: theme.textSub, marginTop: 28, textAlign: 'center', lineHeight: 1.5 }}>
            시작하기를 누르면 이용약관 및 개인정보처리방침에 동의하게 됩니다.
          </p>
        </Fade>
      </div>
    );
  }

  // 회원가입 / 로그인 폼
  const isRegister = mode === 'register';
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      background: `linear-gradient(165deg, ${theme.primaryBg} 0%, #EEEAFF 60%, ${theme.primaryLight} 100%)`,
      padding: 40, minHeight: '100vh',
    }}>
      <Fade show={true}>
        <div style={{
          background: theme.card, borderRadius: 20, padding: '36px 32px',
          width: 380, boxShadow: '0 8px 40px rgba(124,106,175,0.12)',
        }}>
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div style={{ fontSize: 24, fontWeight: 800, color: theme.text, marginBottom: 6 }}>
              {isRegister ? '닉네임 만들기' : '로그인'}
            </div>
            <div style={{ fontSize: 14, color: theme.textSub }}>
              {isRegister ? '사용할 닉네임을 입력해주세요' : '등록한 닉네임을 입력해주세요'}
            </div>
          </div>

          <form onSubmit={isRegister ? handleRegister : handleLogin}>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>닉네임</label>
              <input
                value={nickname}
                onChange={e => setNickname(e.target.value)}
                placeholder="2~12자"
                maxLength={12}
                style={inputStyle}
                autoFocus
              />
              {/* 중복 체크 결과 (회원가입 시만) */}
              {isRegister && nickname.trim().length >= 2 && (
                <div style={{
                  fontSize: 12, marginTop: 6, paddingLeft: 4,
                  color: checking ? theme.textSub : nicknameAvailable ? theme.success : '#C44',
                }}>
                  {checking ? '확인 중...'
                    : nicknameAvailable === true ? '사용 가능한 닉네임이에요!'
                    : nicknameAvailable === false ? '이미 사용 중인 닉네임이에요.'
                    : ''}
                </div>
              )}
            </div>

            {error && (
              <div style={{
                padding: '10px 14px', borderRadius: 10, marginTop: 12,
                background: '#FFF0F0', border: '1px solid #FFD4D4',
                color: '#C44', fontSize: 13, lineHeight: 1.5,
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || (isRegister && nicknameAvailable === false)}
              style={{
                ...btnPrimary, marginTop: 20,
                opacity: (loading || (isRegister && nicknameAvailable === false)) ? 0.6 : 1,
              }}
            >
              {loading ? '처리 중...' : isRegister ? '시작하기' : '로그인'}
            </button>
          </form>

          <div style={{
            textAlign: 'center', marginTop: 20, fontSize: 13, color: theme.textSub,
          }}>
            {isRegister ? (
              <>이미 등록하셨나요? <button onClick={() => { setMode('login'); setError(null); setNickname(''); }} style={{
                background: 'none', border: 'none', color: theme.primary,
                fontWeight: 600, cursor: 'pointer', fontSize: 13,
              }}>로그인</button></>
            ) : (
              <>처음이신가요? <button onClick={() => { setMode('register'); setError(null); setNickname(''); }} style={{
                background: 'none', border: 'none', color: theme.primary,
                fontWeight: 600, cursor: 'pointer', fontSize: 13,
              }}>시작하기</button></>
            )}
          </div>

          <button onClick={() => { setMode('splash'); setError(null); }} style={{
            display: 'block', margin: '16px auto 0', background: 'none',
            border: 'none', color: theme.textSub, fontSize: 13, cursor: 'pointer',
          }}>
            ← 돌아가기
          </button>
        </div>
      </Fade>
    </div>
  );
}
