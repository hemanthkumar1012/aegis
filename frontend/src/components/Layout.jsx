import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Users, FileKey, Activity, CheckSquare, Settings, LogOut, TerminalSquare } from 'lucide-react';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Activity },
    { name: 'Identities', path: '/identities', icon: Users },
    { name: 'Tools', path: '/tools', icon: TerminalSquare },
    { name: 'Policies', path: '/policies', icon: FileKey },
    { name: 'Approvals', path: '/approvals', icon: CheckSquare },
    { name: 'Audit Logs', path: '/audit', icon: Shield },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 flex items-center space-x-2 border-b border-gray-800">
          <Shield className="h-8 w-8 text-blue-500" />
          <span className="text-xl font-bold">Aegis</span>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2 rounded-md transition-colors ${
                  isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 px-3 py-2 w-full text-left text-gray-300 hover:bg-gray-800 rounded-md transition-colors"
          >
            <LogOut className="h-5 w-5" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
