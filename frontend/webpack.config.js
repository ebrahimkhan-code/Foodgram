module.exports = {
    devServer: {
        allowedHosts: ['localhost', '127.0.0.1'],
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:5000',
                changeOrigin: true,
            }
        }
    }
};