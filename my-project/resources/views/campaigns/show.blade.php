<!DOCTYPE html>
<html lang="id" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ $campaign->meta_title ?: $campaign->title }} - {{ $tenant->name }}</title>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- Scripts -->
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
    
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        h1, h2, h3, h4, h5, h6 { font-family: 'Outfit', sans-serif; }
        
        .hero-blur {
            background: radial-gradient(circle at 0% 0%, rgba(79, 70, 229, 0.05) 0%, transparent 50%),
                        radial-gradient(circle at 100% 100%, rgba(6, 182, 212, 0.05) 0%, transparent 50%);
        }
        
        .sticky-form {
            top: 6rem;
        }

        .prose h1, .prose h2, .prose h3 { font-family: 'Outfit', sans-serif; font-weight: 700; color: #0f172a; }
        .prose p { color: #475569; line-height: 1.8; }
    </style>
</head>
<body class="bg-white antialiased text-slate-900 border-t-4 border-indigo-600">

    <!-- Navbar -->
    <nav class="bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-slate-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <div class="flex items-center space-x-3">
                    @if($tenant->logo_path)
                        <img src="{{ Storage::url($tenant->logo_path) }}" alt="{{ $tenant->name }}" class="h-10 w-auto">
                    @endif
                    <span class="text-xl font-black tracking-tight text-slate-900">{{ $tenant->name }}</span>
                </div>
                <div class="hidden md:block">
                    <a href="#register" class="bg-indigo-600 text-white px-8 py-3 rounded-2xl font-bold hover:bg-slate-900 transition-all shadow-lg shadow-indigo-100 hover:shadow-none">Ikut Berpartisipasi</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="hero-blur">
        <!-- Hero Campaign -->
        <section class="relative pt-16 pb-20 overflow-hidden">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid lg:grid-cols-12 gap-16 items-start">
                    
                    <!-- Content Area -->
                    <div class="lg:col-span-8">
                        @if($campaign->image)
                            <div class="rounded-[2.5rem] overflow-hidden shadow-2xl mb-12 border-8 border-white">
                                <img src="{{ Storage::url($campaign->image) }}" alt="{{ $campaign->title }}" class="w-full h-auto">
                            </div>
                        @endif

                        <h1 class="text-4xl md:text-5xl lg:text-6xl font-black text-slate-900 leading-tight mb-8">
                            {{ $campaign->title }}
                        </h1>

                        <div class="prose prose-lg prose-indigo max-w-none campaign-content mb-12">
                            {!! $campaign->landing_page_content !!}
                        </div>
                    </div>

                    <!-- Sidebar Form -->
                    <div class="lg:col-span-4 sticky-form" id="register">
                        <div class="bg-slate-50 rounded-[2.5rem] p-8 md:p-10 border border-slate-100 shadow-xl shadow-slate-100">
                            <h3 class="text-2xl font-bold text-slate-900 mb-2">Formulir Pendaftaran</h3>
                            <p class="text-slate-500 text-sm mb-8">Silakan lengkapi data Anda untuk bergabung dengan program kami.</p>

                            @if(session('success'))
                                <div class="bg-emerald-50 border border-emerald-100 text-emerald-700 p-4 rounded-2xl mb-6 text-sm">
                                    {{ session('success') }}
                                </div>
                            @endif

                            <form action="{{ route('campaign.register', [$tenant->slug, $campaign->slug]) }}" method="POST" class="space-y-5">
                                @csrf
                                <div>
                                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Nama Lengkap</label>
                                    <input type="text" name="name" required class="w-full px-5 py-4 rounded-2xl border-transparent bg-white focus:bg-white focus:ring-2 focus:ring-indigo-500 transition-all text-slate-700 shadow-sm" placeholder="Contoh: Ahmad Abdullah">
                                    @error('name') <p class="mt-1 text-xs text-rose-500">{{ $message }}</p> @enderror
                                </div>

                                <div>
                                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Nomor WhatsApp</label>
                                    <input type="text" name="whatsapp" required class="w-full px-5 py-4 rounded-2xl border-transparent bg-white focus:bg-white focus:ring-2 focus:ring-indigo-500 transition-all text-slate-700 shadow-sm" placeholder="0812XXXXXXXX">
                                    @error('whatsapp') <p class="mt-1 text-xs text-rose-500">{{ $message }}</p> @enderror
                                </div>

                                <div>
                                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Alamat Email</label>
                                    <input type="email" name="email" required class="w-full px-5 py-4 rounded-2xl border-transparent bg-white focus:bg-white focus:ring-2 focus:ring-indigo-500 transition-all text-slate-700 shadow-sm" placeholder="email@contoh.com">
                                    @error('email') <p class="mt-1 text-xs text-rose-500">{{ $message }}</p> @enderror
                                </div>

                                <div class="pt-4">
                                    <button type="submit" class="w-full py-5 bg-indigo-600 hover:bg-slate-900 text-white font-bold rounded-2xl transition-all shadow-lg shadow-indigo-100 transform hover:-translate-y-1">
                                        Kirim Pendaftaran
                                    </button>
                                </div>

                                <p class="text-[10px] text-center text-slate-400 mt-6 px-4">
                                    Dengan mendaftar, Anda menyetujui ketentuan layanan dan akan dihubungi oleh tim kami melalui WhatsApp.
                                </p>
                            </form>
                        </div>
                    </div>

                </div>
            </div>
        </section>
    </main>

    <footer class="bg-slate-900 py-12 text-white border-t border-slate-800">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-400 text-sm">
            <p>© 2026 {{ $tenant->name }}. Dikelola dengan sistem Pondok Indonesia.</p>
        </div>
    </footer>

</body>
</html>
