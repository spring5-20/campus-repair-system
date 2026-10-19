import { useState } from 'react';
import { App, Button, Form, Input, Typography } from 'antd';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { login as loginRequest } from '@/api/auth/login';
import { setAuthToken } from '@/api/client';
import { getRoleHomePath } from '@/routes/config.js';

/**
 * 登录页：根据设计稿还原校园报修协同系统登录界面
 */
export const LoginPage = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();



  const onFinish = async (values) => {
    setSubmitting(true);

    try {
      const response = await loginRequest(values);

      const payload = response?.data || response;
      const user = payload?.user || payload;
      const token = payload?.token || response?.token || '';

      if (!user || typeof user !== 'object') {
        throw new Error('登录失败，返回数据异常');
      }

      const role = String(user.role || '').toLowerCase();
      const firstRouteByRole = getRoleHomePath(role);
      const redirectPath = location.state?.from || firstRouteByRole;

      if (token) {
        setAuthToken(token);
      }

      localStorage.setItem('reac-admin-auth', JSON.stringify(user));
      message.success('登录成功');
      navigate(redirectPath, { replace: true });
    } catch (error) {
      const errorMessage = error?.message || '登录失败，请检查用户名和密码';
      message.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="login-page"
      style={{
        minHeight: '100vh',
        display: 'flex',
        background: '#e8efe9',
      }}
    >
      <div
        className="login-page__visual"
        style={{
          flex: '0 0 46%',
          minHeight: '100vh',
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(180deg, #0a4d4a 0%, #0d5c57 100%)',
          overflow: 'hidden',
          padding: '48px 56px',
        }}
      >
        <div
          style={{
            position: 'absolute',
            width: '560px',
            height: '560px',
            borderRadius: '50%',
            border: '1px solid rgba(237, 205, 130, 0.25)',
            right: '-120px',
            top: '50%',
            transform: 'translateY(-50%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: '760px',
            height: '760px',
            borderRadius: '50%',
            border: '1px solid rgba(237, 205, 130, 0.18)',
            left: '-160px',
            top: '14%',
          }}
        />

        <div style={{ position: 'relative', width: '100%', maxWidth: 540, zIndex: 1 }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: 18,
              background: 'linear-gradient(180deg, #f0d38b 0%, #dcae4a 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#0b4c45',
              fontSize: 28,
              fontWeight: 700,
              marginBottom: 32,
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.12)',
            }}
          >
            修
          </div>

          <Typography.Title
            className="login-page__title"
            level={1}
            style={{
              margin: 0,
              color: '#f4f7f6',
              fontWeight: 700,
              fontSize: 52,
              lineHeight: 1.18,
              letterSpacing: 0,
            }}
          >
            校园报修协同系统
          </Typography.Title>

          <Typography.Paragraph
            style={{
              marginTop: 18,
              fontSize: 16,
              lineHeight: 1.8,
              color: 'rgba(255,255,255,0.75)',
              maxWidth: 520,
            }}
          >
            从学生发起报修，到维修人员接单处理，再到学生验收关闭，
            用一个项目联动完成前后端业务闭环。
          </Typography.Paragraph>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 24 }}>
            {['学生提报修', '维修接单', '完成维修', '学生验收'].map((label) => (
              <span
                key={label}
                style={{
                  border: '1px solid rgba(255,255,255,0.25)',
                  background: 'rgba(255,255,255,0.04)',
                  color: '#eff7f4',
                  borderRadius: 8,
                  padding: '7px 12px',
                  fontSize: 13,
                }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div
        className="login-page__panel"
        style={{
          flex: 1,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#ececeb',
          padding: '32px 20px',
        }}
      >
        <div
          className="login-page__card"
          style={{
            width: '100%',
            maxWidth: 420,
            background: 'rgba(245, 245, 243, 0.9)',
            borderRadius: 22,
            padding: '32px 28px',
            boxShadow: '0 16px 32px rgba(36, 62, 56, 0.1)',
            border: '1px solid rgba(105, 118, 111, 0.08)',
            margin: '0 auto',
          }}
        >
          <Typography.Text
            style={{
              display: 'block',
              textAlign: 'center',
              color: '#8d8a78',
              letterSpacing: '0.2em',
              fontSize: 12,
              marginBottom: 12,
            }}
          >
            MINI REPAIR SYSTEM
          </Typography.Text>

          <Typography.Title
            level={2}
            style={{
              textAlign: 'center',
              margin: '0 0 8px',
              color: '#1a2d2a',
              fontWeight: 700,
            }}
          >
            登录
          </Typography.Title>
          <Form
            form={form}
            name="login"
            size="large"
            onFinish={onFinish}
            layout="vertical"
            style={{ marginTop: 6, maxWidth: 360, marginLeft: 'auto', marginRight: 'auto' }}
          >
            <Form.Item
              label={<span style={{ color: '#4f5652', fontSize: 16, fontWeight: 600 }}>用户名</span>}
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
              style={{ marginBottom: 18 }}
            >
              <Input
                prefix={<UserOutlined style={{ color: '#9aa2a0' }} />}
                placeholder="请输入用户名"
                autoComplete="username"
                style={{
                  height: 52,
                  borderRadius: 12,
                  border: '1px solid #d9ddd8',
                  background: '#f8f9f8',
                }}
              />
            </Form.Item>

            <Form.Item
              label={<span style={{ color: '#4f5652', fontSize: 16, fontWeight: 600 }}>密码</span>}
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
              style={{ marginBottom: 26 }}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: '#9aa2a0' }} />}
                placeholder="请输入密码"
                autoComplete="current-password"
                style={{
                  height: 52,
                  borderRadius: 12,
                  border: '1px solid #d9ddd8',
                  background: '#f8f9f8',
                }}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 18 }}>
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={submitting}
                style={{
                  height: 56,
                  borderRadius: 12,
                  background: 'linear-gradient(180deg, #0f625f 0%, #0b4948 100%)',
                  border: 'none',
                  fontSize: 18,
                  fontWeight: 600,
                  boxShadow: '0 12px 24px rgba(20, 92, 86, 0.22)',
                }}
              >
                登录系统
              </Button>
            </Form.Item>
          </Form>
        </div>
      </div>
    </div>
  );
};
