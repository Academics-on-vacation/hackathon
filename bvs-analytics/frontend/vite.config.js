import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    // ????????? ??? ??????
    build: {
        outDir: 'dist',
        assetsDir: 'assets', // ??? ?????? ????? ? ????? assets
        rollupOptions: {
            output: {
                // ??? JS ? CSS ????? ????? ? assets
                chunkFileNames: 'assets/js/[name]-[hash].js',
                entryFileNames: 'assets/js/[name]-[hash].js',
                assetFileNames: ({name}) => {
                    if (/\.(css)$/.test(name ?? '')) {
                        return 'assets/css/[name]-[hash][extname]'
                    }
                    if (/\.(png|jpe?g|gif|svg|webp|avif)$/.test(name ?? '')) {
                        return 'assets/img/[name]-[hash][extname]'
                    }
                    if (/\.(woff|woff2|eot|ttf|otf)$/.test(name ?? '')) {
                        return 'assets/fonts/[name]-[hash][extname]'
                    }
                    return 'assets/[name]-[hash][extname]'
                }
            }
        }
    },
    base: process.env.NODE_ENV === 'production' ? '/' : '/',
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            }
        }
    }
})