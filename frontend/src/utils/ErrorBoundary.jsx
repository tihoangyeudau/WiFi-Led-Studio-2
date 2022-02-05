import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI.
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        // logErrorToMyService(error, errorInfo);
        console.log(error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return <div style={{
                maxWidth: 360, width: '100%', display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                textAlign: 'center',
                margin: '0 auto',
                paddingTop: '3rem'
            }}>
                <h1>Đã xảy ra sự cố</h1>
                <p>
                    Xóa dữ liệu giao diện người dùng của trình duyệt có thể hữu ích,<br />
                    nếu còn lại dữ liệu cấu hình cũ.
                </p>
                <p> Làm mới trang sau khi xóa dữ liệu... </p>
                <button style={{ height: 40, borderRadius: 10, border: '1px solid #999', color: '#fff', backgroundColor: '#600000', cursor: 'pointer'}} onClick={() => {
                    window.localStorage.removeItem('undefined')
                    window.localStorage.removeItem('wls-host')
                    window.localStorage.removeItem('wls-hosts')
                    window.localStorage.removeItem('wls-frontend')
                    window.localStorage.removeItem('wls-cloud-role')
                    window.localStorage.removeItem('wls-cloud-userid')
                    window.localStorage.removeItem('wls-theme')
                    window.localStorage.removeItem('jwt')
                    window.localStorage.removeItem('username')
                    window.localStorage.removeItem('BladeMod')
                    window.location.reload()
                }}>Xóa dữ liệu trình duyệt</button><br />            
            </div>;
        }

        return this.props.children;
    }
}

export default ErrorBoundary