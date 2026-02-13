<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="scroll-smooth">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Blog & Wawasan - {{ config('app.name', 'Pondok Indonesia') }}</title>
    
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
            body { @apply font-sans antialiased bg-slate-50 text-slate-900; }
            h1, h2, h3, h4, h5, h6 { @apply font-outfit; }
        }
        
        .glass-nav {
            @apply bg-white/75 backdrop-blur-xl border-b border-slate-100;
        }
        
        .card-blog {
            @apply bg-white border border-slate-100 transition-all duration-500;
        }
        
        .card-blog:hover {
            @apply -translate-y-2 shadow-2xl shadow-indigo-100/30 border-indigo-100/50;
        }

        .text-gradient {
            @apply bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-cyan-500;
        }
    </style>
</head>
<body>

    <!-- Header / Navbar -->
    <header class="fixed w-full z-50 glass-nav">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-20">
                <a href="/" class="flex items-center">
                    <span class="text-2xl font-extrabold tracking-tight">
                        <span class="text-indigo-600">Pondok</span><span class="text-slate-900 font-outfit">Indonesia</span>
                    </span>
                </a>
                
                <nav class="hidden md:flex items-center space-x-10">
                    <a href="/" class="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Home</a>
                    <a href="{{ route('blog.index') }}" class="text-sm font-bold text-indigo-600">Blog</a>
                    <a href="{{ route('filament.admin.auth.login') }}" class="text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Masuk</a>
                </nav>

                <div class="flex items-center">
                    <a href="{{ route('registration.form') }}" class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-sm font-bold rounded-xl text-white bg-indigo-600 hover:bg-slate-900 transition-all shadow-lg shadow-indigo-200">
                        Daftar Akun
                    </a>
                </div>
            </div>
        </div>
    </header>

    <main class="pt-32 pb-24">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-20">
                <h1 class="text-5xl font-black text-slate-900 mb-6 font-outfit text-gradient">Wawasan & Update</h1>
                <p class="text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto">
                    Strategi pengelolaan pesantren modern dan teknologi terbaru.
                </p>
            </div>

            @if($posts->count() > 0)
                <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-10">
                    @foreach($posts as $post)
                        <article class="card-blog rounded-[2.5rem] overflow-hidden group">
                            <a href="{{ route('blog.show', $post->slug) }}" class="block relative aspect-[16/10] overflow-hidden bg-slate-200">
                                @if($post->image)
                                    <img src="{{ Storage::url($post->image) }}" alt="{{ $post->title }}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110">
                                @else
                                    <div class="w-full h-full flex items-center justify-center">
                                        <svg class="w-12 h-12 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                                    </div>
                                @endif
                            </a>
                            
                            <div class="p-8">
                                <div class="flex items-center space-x-3 mb-4">
                                    <span class="px-3 py-1 bg-indigo-50 text-indigo-600 text-[10px] font-bold rounded-full uppercase tracking-widest">Artikel</span>
                                    <span class="text-slate-400 text-xs font-medium">{{ $post->published_at ? $post->published_at->format('d M Y') : 'Draft' }}</span>
                                </div>
                                <h2 class="text-2xl font-bold mb-4 line-clamp-2 leading-snug group-hover:text-indigo-600 transition-colors font-outfit">
                                    <a href="{{ route('blog.show', $post->slug) }}">{{ $post->title }}</a>
                                </h2>
                                <p class="text-slate-500 text-sm leading-relaxed line-clamp-3 mb-8">
                                    {{ Str::limit(strip_tags($post->content), 120) }}
                                </p>
                                <a href="{{ route('blog.show', $post->slug) }}" class="inline-flex items-center text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                                    Selengkapnya
                                    <svg class="ml-2 w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path></svg>
                                </a>
                            </div>
                        </article>
                    @endforeach
                </div>

                <div class="mt-16">
                    {{ $posts->links() }}
                </div>
            @else
                <div class="text-center py-32 bg-white rounded-[3rem] border border-slate-100">
                    <p class="text-xl font-bold text-slate-400">Belum ada artikel.</p>
                </div>
            @endif
        </div>
    </main>

    <footer class="bg-slate-900 py-12 text-white/50 text-sm text-center">
        <p>© 2026 {{ config('app.name') }}. All rights reserved.</p>
    </footer>
</body>
</html>
