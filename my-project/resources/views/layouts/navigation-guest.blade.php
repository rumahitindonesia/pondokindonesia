<nav x-data="{ open: false }" class="bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-20">
            <div class="flex items-center">
                <a href="/" class="flex items-center space-x-2">
                    <span class="text-2xl font-black tracking-tighter text-indigo-600">PONDOK</span>
                    <span class="text-2xl font-light tracking-tighter text-gray-400">INDONESIA</span>
                </a>
            </div>

            <!-- Desktop Menu -->
            <div class="hidden md:flex items-center space-x-10">
                <a href="#fitur" class="text-sm font-semibold text-gray-500 hover:text-indigo-600 transition">Fitur</a>
                <a href="#layanan" class="text-sm font-semibold text-gray-500 hover:text-indigo-600 transition">Layanan</a>
                <a href="{{ route('blog.index') }}" class="text-sm font-semibold text-gray-500 hover:text-indigo-600 transition">Blog</a>
                <a href="#kontak" class="text-sm font-semibold text-gray-500 hover:text-indigo-600 transition">Kontak</a>
                
                @if (Route::has('login'))
                    @auth
                        <a href="{{ url('/admin') }}" class="text-sm font-medium text-gray-600 hover:text-indigo-600">Dashboard</a>
                    @else
                        <a href="{{ route('login') }}" class="text-sm font-medium text-gray-600 hover:text-indigo-600">Masuk</a>
                        <a href="#daftar" class="inline-flex items-center px-5 py-2.5 border border-transparent text-sm font-semibold rounded-full text-white bg-indigo-600 hover:bg-indigo-700 shadow-md transform hover:-translate-y-0.5 transition duration-150">
                            Bergabung
                        </a>
                    @endauth
                @endif
            </div>

            <!-- Mobile Burger Icon -->
            <div class="md:hidden flex items-center">
                <button @click="open = ! open" type="button" class="text-gray-500 hover:text-gray-600 focus:outline-none p-2">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path :class="{'hidden': open, 'inline-flex': ! open }" class="inline-flex" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        <path :class="{'hidden': ! open, 'inline-flex': open }" class="hidden" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <!-- Mobile Menu Container -->
    <div x-show="open" 
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0 -translate-y-2"
         x-transition:enter-end="opacity-100 translate-y-0"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100 translate-y-0"
         x-transition:leave-end="opacity-0 -translate-y-2"
         class="md:hidden bg-white border-b border-gray-100 px-4 pt-2 pb-6 space-y-2 shadow-xl"
         style="display: none;">
        <a href="#fitur" @click="open = false" class="block px-3 py-2 text-base font-semibold text-gray-600 hover:text-indigo-600 hover:bg-gray-50 rounded-lg">Fitur</a>
        <a href="#layanan" @click="open = false" class="block px-3 py-2 text-base font-semibold text-gray-600 hover:text-indigo-600 hover:bg-gray-50 rounded-lg">Layanan</a>
        <a href="{{ route('blog.index') }}" class="block px-3 py-2 text-base font-semibold text-gray-600 hover:text-indigo-600 hover:bg-gray-50 rounded-lg">Blog</a>
        <a href="#kontak" @click="open = false" class="block px-3 py-2 text-base font-semibold text-gray-600 hover:text-indigo-600 hover:bg-gray-50 rounded-lg">Kontak</a>
        <hr class="border-gray-100">
        @if (Route::has('login'))
            @auth
                <a href="{{ url('/admin') }}" class="block px-3 py-2 text-base font-medium text-indigo-600">Dashboard</a>
            @else
                <a href="{{ route('login') }}" class="block px-3 py-2 text-base font-medium text-gray-600">Masuk</a>
                <a href="#daftar" @click="open = false" class="block px-3 py-2 text-base font-bold text-center bg-indigo-600 text-white rounded-lg shadow-md mt-4">
                    Bergabung
                </a>
            @endauth
        @endif
    </div>
</nav>
