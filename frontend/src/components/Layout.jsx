import { theme as defaultTheme, getTheme } from '../styles/theme';

export const Fade = ({ show, children, delay = 0 }) => (
  <div style={{
    opacity: show ? 1 : 0,
    transform: show ? 'translateY(0)' : 'translateY(12px)',
    transition: `all 0.4s cubic-bezier(0.22,1,0.36,1) ${delay}ms`,
  }}>
    {children}
  </div>
);

export const Header = ({ title, subtitle, showBack, onBack, right, mode }) => {
  const theme = mode ? getTheme(mode) : defaultTheme;
  return (
  <div style={{
    padding: '14px 24px 10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: theme.bg,
    position: 'sticky',
    top: 0,
    zIndex: 5,
    margin: '0 -24px',
    width: 'calc(100% + 48px)',
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      {showBack && (
        <button onClick={onBack} style={{
          background: 'none', border: 'none', fontSize: 20,
          cursor: 'pointer', color: theme.primary, padding: 4, lineHeight: 1,
        }}>←</button>
      )}
      <div>
        <div style={{ fontSize: 18, fontWeight: 700, color: theme.text, letterSpacing: -0.3 }}>{title}</div>
        {subtitle && <div style={{ fontSize: 12, color: theme.textSub, marginTop: 2 }}>{subtitle}</div>}
      </div>
    </div>
    {right}
  </div>
  );
};

export const TopNav = ({ active, setTab, userName, userEmail, onLogout, mode, isGuest }) => {
  const theme = mode ? getTheme(mode) : defaultTheme;
  const tabs = [
    { id: 'chat', icon: '💬', label: '채팅' },
    { id: 'records', icon: '📋', label: '기록' },
    { id: 'calc', icon: '✨', label: '지원금' },
  ];
  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      borderBottom: `1px solid ${theme.border}`,
      background: theme.card,
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 10,
      gap: 4,
    }}>
      <div className="topnav-brand" onClick={() => setTab('home')} style={{
        fontSize: 20, fontWeight: 700, color: theme.primary,
        marginRight: 28, padding: '14px 0',
        letterSpacing: -0.5, flexShrink: 0, cursor: 'pointer',
        fontStyle: 'italic',
      }}>lyle</div>
      <div style={{ flex: 1, display: 'flex', gap: 4, overflow: 'auto' }}>
      {tabs.map(t => (
        <button key={t.id} className="topnav-tab" onClick={() => setTab(t.id)} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: active === t.id ? theme.primaryLight : 'none',
          border: 'none', cursor: 'pointer',
          padding: '8px 16px', flexShrink: 0,
          borderRadius: 20,
          transition: 'all 0.2s',
        }}>
          <span style={{
            fontSize: 15,
            opacity: active === t.id ? 1 : 0.6,
          }}>{t.icon}</span>
          <span className="topnav-label" style={{
            fontSize: 14,
            fontWeight: active === t.id ? 600 : 400,
            color: active === t.id ? theme.primary : theme.textSub,
          }}>{t.label}</span>
        </button>
      ))}
      </div>
      {!isGuest ? (
      <div
        className="topnav-user"
        onClick={() => setTab('mypage')}
        style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', flexShrink: 0 }}
      >
        <div style={{
          width: 28, height: 28, borderRadius: 8,
          background: `linear-gradient(135deg, ${theme.primary}, ${theme.accent})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, color: '#fff', fontWeight: 700,
        }}>{(userName || userEmail || '?')[0].toUpperCase()}</div>
        <span className="topnav-user-name" style={{ fontSize: 13, color: theme.text, fontWeight: 500 }}>
          {userName || userEmail || ''}
        </span>
      </div>
      ) : (
      <div className="topnav-user" style={{ flexShrink: 0 }}>
        <span style={{ fontSize: 12, color: theme.textSub }}>게스트</span>
      </div>
      )}
    </nav>
  );
};

export const AppShell = ({ children, mode }) => {
  const theme = mode ? getTheme(mode) : defaultTheme;
  return (
  <div style={{
    width: '100%',
    minHeight: '100vh',
    background: theme.bg,
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
  }}>
    {children}
  </div>
  );
};
