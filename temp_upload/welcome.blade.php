<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="scroll-smooth">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ config('app.name', 'Pondok Indonesia') }} - Membangun Masa Depan Pesantren Modern</title>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- CSS / Tailwind CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: {
                            50: '#f5f3ff',
                            100: '#ede9fe',
                            200: '#ddd6fe',
                            300: '#c4b5fd',
                            400: '#a78bfa',
                            500: '#8b5cf6',
                            600: '#7c3aed',
                            700: '#6d28d9',
                            800: '#5b21b6',
                            900: '#4c1d95',
                            950: '#2e1065',
                        },
                    },
                    fontFamily: {
                        sans: ['Plus Jakarta Sans', 'sans-serif'],
                        outfit: ['Outfit', 'sans-serif'],
                    },
                }
            }
        }
    </script>
    
    <style type="text/tailwindcss">
        @layer base {
            body { @apply font-sans antialiased bg-white text-slate-900; }
            h1, h2, h3, h4, h5, h6 { @apply font-outfit; }
        }
        
        @layer components {
            .glass-nav {
                @apply bg-white/75 backdrop-blur-xl border-b border-slate-100/50;
            }
            
            .hero-gradient {
                background: radial-gradient(circle at 0% 0%, rgba(79, 70, 229, 0.08) 0%, transparent 50%),
                            radial-gradient(circle at 100% 100%, rgba(6, 182, 212, 0.08) 0%, transparent 50%);
            }
            
            .card-premium {
                @apply bg-white border border-slate-100 transition-all duration-500 overflow-hidden relative;
            }
            
            .card-premium:hover {
                @apply -translate-y-2 shadow-2xl shadow-indigo-100/50 border-indigo-200/50;
            }

            .text-gradient {
                @apply bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-cyan-500;
            }

            .btn-primary {
                @apply inline-flex items-center justify-center px-10 py-5 bg-indigo-600 hover:bg-slate-900 text-white text-lg font-bold rounded-2xl transition-all shadow-2xl hover:shadow-indigo-300 transform hover:-translate-y-1;
            }

            .section-title {
                @apply text-4xl md:text-5xl font-black text-slate-900 leading-tight tracking-tight mb-6;
            }
        }
    </style>
</head>
<body class="hero-gradient">

    <!-- Header / Navbar -->
    <header class="fixed w-full z-50 glass-nav">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-20">
                <div class="flex items-center">
                    <span class="text-2xl font-extrabold tracking-tight">
                        <span class="text-indigo-600">Pondok</span><span class="text-slate-900">Indonesia</span>
                    </span>
                </div>
                
                <nav class="hidden md:flex items-center space-x-10">
                    <a href="#solusi" class="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Solusi</a>
                    <a href="#manfaat" class="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Manfaat</a>
                    <a href="#pricing" class="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Harga</a>
                    <a href="{{ route('blog.index') }}" class="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Blog</a>
                </nav>

                <div class="flex items-center space-x-5">
                    <a href="{{ route('filament.admin.auth.login') }}" class="text-sm font-bold text-slate-700 hover:text-indigo-600 transition-colors">Masuk</a>
                    <a href="{{ route('registration.form') }}" class="btn-primary !px-6 !py-3 !text-sm !shadow-lg">
                        Mulai Gratis
                    </a>
                </div>
            </div>
        </div>
    </header>

    <main>
        <!-- Hero Section -->
        <section class="pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
                <div class="text-center max-w-5xl mx-auto mb-16">
                    <div class="inline-flex items-center px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 mb-8">
                        <span class="flex h-2 w-2 rounded-full bg-indigo-500 mr-3"></span>
                        <span class="text-[10px] font-bold text-indigo-700 uppercase tracking-widest leading-none">Sinergi Tradisi & Teknologi Modern</span>
                    </div>
                    
                    <h1 class="text-6xl md:text-7xl lg:text-8xl font-black text-slate-900 leading-[1.05] tracking-tight mb-8">
                        Jalin Silaturahmi <span class="text-gradient">Lebih Hangat</span>, Wujudkan Kemandirian Pesantren.
                    </h1>
                    
                    <p class="text-xl md:text-2xl text-slate-600 mb-12 leading-relaxed max-w-3xl mx-auto">
                        Sentuhan personal AI untuk menjaga hubungan erat dengan wali santri dan donatur, otomatis 24/7.
                    </p>
                    
                    <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <a href="{{ route('registration.form') }}" class="btn-primary w-full sm:w-auto">
                            Demo Gratis Sekarang
                        </a>
                        <a href="#solusi" class="w-full sm:w-auto px-10 py-5 border-2 border-slate-200 hover:border-indigo-600 hover:text-indigo-600 text-slate-800 text-lg font-bold rounded-2xl transition-all">
                            Kenali Lebih Lanjut
                        </a>
                    </div>
                </div>

                <!-- Dashboard Preview -->
                <div class="relative max-w-5xl mx-auto mt-20">
                    <div class="absolute -inset-4 bg-gradient-to-r from-indigo-500 to-cyan-400 opacity-20 blur-2xl rounded-[3rem]"></div>
                    <img src="{{ asset('images/home/dashboard.png') }}" alt="Dashboard Mockup" class="relative rounded-[2.5rem] shadow-2xl border border-white/50 w-full object-cover aspect-video">
                </div>
            </div>
        </section>

        <!-- Social Proof / Partners -->
        <section class="py-12 border-y border-slate-100 bg-slate-50/30">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <p class="text-center text-xs font-bold text-slate-400 uppercase tracking-widest mb-8">Amanah Bagi Pesantren Terkemuka</p>
                <div class="flex flex-wrap justify-center items-center gap-10 md:gap-20 opacity-40 grayscale hover:grayscale-0 transition-all duration-500">
                    <span class="text-xl font-black text-slate-700">NU ONLINE</span>
                    <span class="text-xl font-black text-slate-700">BAZNAS</span>
                    <span class="text-xl font-black text-slate-700">PESANTREN AL-HIKMAH</span>
                    <span class="text-xl font-black text-slate-700">YAYASAN AMAL</span>
                </div>
            </div>
        </section>

        <!-- Problem & Solution Section -->
        <section id="solusi" class="py-24 lg:py-32">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid lg:grid-cols-2 gap-20 items-center">
                    <div>
                        <h2 class="section-title">Lelah Kirim Pesan <span class="text-rose-500 underline decoration-indigo-200">Manual</span> ke Ribuan Donatur?</h2>
                        <p class="text-lg text-slate-600 mb-8 leading-relaxed">
                            Mengelola ratusan santri dan donatur secara tradisional sangat melelahkan. Kami hadir untuk mengotomatisasi silaturahmi Anda.
                        </p>
                        
                        <div class="space-y-6">
                            <div class="flex gap-4">
                                <div class="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center flex-shrink-0">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                </div>
                                <div>
                                    <h4 class="text-xl font-bold mb-1">Cepat & Personal</h4>
                                    <p class="text-slate-500">AI kami memahami konteks setiap donatur dan menyapa mereka dengan hangat.</p>
                                </div>
                            </div>
                            <div class="flex gap-4">
                                <div class="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center flex-shrink-0">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                </div>
                                <div>
                                    <h4 class="text-xl font-bold mb-1">Kemandirian Ekonomi</h4>
                                    <p class="text-slate-500">Sistem pendaftaran & donasi terintegrasi untuk pendanaan pesantren yang stabil.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="relative">
                        <img src="{{ asset('images/home/comparison.png') }}" alt="AI Comparison" class="rounded-[2.5rem] shadow-2xl w-full">
                        <div class="absolute -bottom-8 -left-8 bg-white p-6 rounded-3xl shadow-xl border border-slate-100 max-w-xs md:block hidden animate-bounce">
                            <p class="text-sm font-bold text-slate-900 mb-1">"Sentuhan AI sangat nyata."</p>
                            <p class="text-xs text-indigo-600 font-medium">Ustadz Hanan, Ponpes Az-Zahra</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Benefits Section -->
        <section id="manfaat" class="py-24 bg-slate-900 text-white rounded-[3rem] lg:rounded-[5rem] mx-4 overflow-hidden relative">
            <div class="absolute inset-0 opacity-10">
                <div class="absolute top-0 right-0 w-96 h-96 bg-indigo-500 rounded-full filter blur-[100px]"></div>
                <div class="absolute bottom-0 left-0 w-96 h-96 bg-cyan-500 rounded-full filter blur-[100px]"></div>
            </div>
            
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div class="text-center max-w-3xl mx-auto mb-20">
                    <h2 class="text-4xl md:text-5xl font-black mb-6 font-outfit">Sinergi Tradisi & Efisiensi</h2>
                    <p class="text-indigo-200 text-lg">Wujudkan tata kelola pesantren yang profesional dan transparan.</p>
                </div>

                <div class="grid md:grid-cols-3 gap-10">
                    <div class="p-8 border border-white/10 rounded-3xl bg-white/5 backdrop-blur-sm">
                        <h4 class="text-5xl font-black text-indigo-400 mb-4">10+</h4>
                        <h5 class="text-xl font-bold mb-2">Jam Dihemat/Minggu</h5>
                        <p class="text-slate-400 text-sm">Otomatisasi laporan dan pesan rutin membebaskan pengurus dari tugas admin yang membosankan.</p>
                    </div>
                    <div class="p-8 border border-white/10 rounded-3xl bg-white/5 backdrop-blur-sm">
                        <h4 class="text-5xl font-black text-cyan-400 mb-4">3x</h4>
                        <h5 class="text-xl font-bold mb-2">Peningkatan Donasi</h5>
                        <p class="text-slate-400 text-sm">Follow-up donatur yang hangat terbukti meningkatkan retensi dan nominal donasi secara berkelanjutan.</p>
                    </div>
                    <div class="p-8 border border-white/10 rounded-3xl bg-white/5 backdrop-blur-sm">
                        <h4 class="text-5xl font-black text-emerald-400 mb-4">100%</h4>
                        <h5 class="text-xl font-bold mb-2">Transparansi Data</h5>
                        <p class="text-slate-400 text-sm">Akses data wali santri dan donatur secara real-time untuk pengambilan keputusan yang lebih tepat.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Pricing Section -->
        <section id="pricing" class="py-24 lg:py-32">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-20">
                    <h2 class="section-title">Pilih Paket Kebaikan Anda</h2>
                    <p class="text-slate-500 text-lg">Mulai dengan gratis, tingkatkan seiring perkembangan pesantren Anda.</p>
                </div>

                <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    <!-- Freemium -->
                    <div class="card-premium p-10 rounded-[2.5rem] border-2 border-transparent hover:border-slate-100">
                        <h3 class="text-xl font-bold mb-2">Paket Amanah (Free)</h3>
                        <div class="flex items-baseline mb-6">
                            <span class="text-4xl font-black text-slate-900">Rp 0</span>
                            <span class="text-slate-400 ml-2">/ selamanya</span>
                        </div>
                        <ul class="space-y-4 mb-10 text-slate-600 font-medium">
                            <li class="flex items-center"><svg class="w-5 h-5 text-emerald-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg> 500 Pesan WhatsApp / Bulan</li>
                            <li class="flex items-center"><svg class="w-5 h-5 text-emerald-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg> Manajemen Donatur Dasar</li>
                            <li class="flex items-center"><svg class="w-5 h-5 text-emerald-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg> 1 Campaign Pembangunan</li>
                        </ul>
                        <a href="{{ route('registration.form') }}" class="block text-center py-4 px-6 border-2 border-slate-100 font-bold rounded-2xl hover:bg-slate-50 transition-all">Mulai Sekarang</a>
                    </div>

                    <!-- Pro -->
                    <div class="card-premium p-10 rounded-[2.5rem] border-2 border-indigo-600 shadow-2xl shadow-indigo-100">
                        <div class="absolute top-6 right-6 px-3 py-1 bg-indigo-600 text-white text-[10px] font-bold rounded-full uppercase tracking-widest">Paling Populer</div>
                        <h3 class="text-xl font-bold mb-2">Paket Berkah (Pro)</h3>
                        <div class="flex items-baseline mb-6">
                            <span class="text-4xl font-black text-slate-900">Chat CS</span>
                            <span class="text-slate-400 ml-2">/ terjangkau</span>
                        </div>
                        <ul class="space-y-4 mb-10 text-slate-600 font-medium">
                            <li class="flex items-center"><svg class="w-5 h-5 text-indigo-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg> Pesan Tanpa Batas</li>
                            <li class="flex items-center text-slate-900 tracking-tight"><svg class="w-5 h-5 text-indigo-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg> Integrasi Personal AI (Groq/Gemini)</li>
                            <li class="flex items-center"><svg class="w-5 h-5 text-indigo-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg> Dashboard Analisis Prediktif</li>
                            <li class="flex items-center"><svg class="w-5 h-5 text-indigo-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg> Multi-Campaign & Payroll</li>
                        </ul>
                        <a href="https://wa.me/628123456789" class="block text-center py-4 px-6 bg-indigo-600 text-white font-bold rounded-2xl hover:bg-slate-900 transition-all shadow-lg shadow-indigo-200">Hubungi Konsultan Kami</a>
                    </div>
                </div>
            </div>
        </section>

        <!-- Final CTA Section -->
        <section class="py-24 bg-indigo-50/50">
            <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h2 class="text-4xl md:text-5xl font-black text-slate-900 mb-8 font-outfit">Bersama Majukan Pesantren Indonesia</h2>
                <p class="text-xl text-slate-600 mb-10">Daftarkan pesantren Anda hari ini dan rasakan kemudahan mengelola ummat dengan teknologi.</p>
                <a href="{{ route('registration.form') }}" class="btn-primary">Daftar Akun Pesantren - Gratis</a>
            </div>
        </section>

        <!-- Footer -->
        <footer class="bg-slate-900 pt-20 pb-10 text-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid md:grid-cols-4 gap-12 mb-16">
                    <div class="col-span-2">
                        <span class="text-2xl font-extrabold tracking-tight block mb-6">
                            <span class="text-indigo-400">Pondok</span><span>Indonesia</span>
                        </span>
                        <p class="text-slate-500 max-w-sm leading-relaxed">Platform digital terdepan untuk modernisasi dan kemandirian ekonomi pesantren melalui kecerdasan buatan.</p>
                    </div>
                    <div>
                        <h4 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">Platform</h4>
                        <ul class="space-y-4 text-slate-500 font-medium">
                            <li><a href="#solusi" class="hover:text-white transition-colors">Solusi Digital</a></li>
                            <li><a href="{{ route('blog.index') }}" class="hover:text-white transition-colors">Wawasan & Blog</a></li>
                            <li><a href="#pricing" class="hover:text-white transition-colors">Daftar Harga</a></li>
                        </ul>
                    </div>
                    <div>
                        <h4 class="font-bold mb-6 uppercase text-xs tracking-widest text-slate-400">Bantuan</h4>
                        <ul class="space-y-4 text-slate-500 font-medium">
                            <li><a href="#" class="hover:text-white transition-colors">Pusat Bantuan</a></li>
                            <li><a href="#" class="hover:text-white transition-colors">Kontak Kami</a></li>
                            <li><a href="#" class="hover:text-white transition-colors">Demo Produk</a></li>
                        </ul>
                    </div>
                </div>
                <div class="border-t border-slate-800 pt-10 flex flex-col md:flex-row justify-between items-center text-slate-500 text-sm">
                    <p>© 2026 {{ config('app.name') }}. Didukung oleh Pondok IT Indonesia.</p>
                    <div class="flex space-x-6 mt-4 md:mt-0">
                        <a href="#" class="hover:text-indigo-400 transition-colors">Syarat & Ketentuan</a>
                        <a href="#" class="hover:text-indigo-400 transition-colors">Kebijakan Privasi</a>
                    </div>
                </div>
            </div>
        </footer>
    </main>
</body>
</html>
