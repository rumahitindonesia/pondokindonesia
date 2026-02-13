<x-guest-layout>
    <x-slot name="title">
        {{ $tenant->name }} - Profil Lembaga
    </x-slot>

    <div class="relative min-h-[60vh] flex items-center justify-center overflow-hidden bg-gray-50 pt-20">
        <!-- Background Decorations -->
        <div class="absolute inset-0 z-0 opacity-10">
            <div class="absolute -top-1/2 -left-1/4 w-[1000px] h-[1000px] rounded-full bg-indigo-500 blur-3xl"></div>
            <div class="absolute top-full -right-1/4 w-[800px] h-[800px] rounded-full bg-pink-400 blur-3xl"></div>
        </div>

        <div class="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
            @if($tenant->logo_path)
                <div class="mb-8 flex justify-center">
                    <img src="{{ Storage::url($tenant->logo_path) }}" alt="{{ $tenant->name }}" class="h-32 w-32 object-contain rounded-2xl bg-white p-4 shadow-xl ring-1 ring-gray-100">
                </div>
            @endif
            
            <h1 class="text-4xl md:text-6xl font-black text-gray-900 tracking-tight mb-6">
                {{ $tenant->name }}
            </h1>
            
            <div class="max-w-3xl mx-auto">
                <p class="text-xl text-gray-600 leading-relaxed mb-10">
                    {{ $tenant->description ?: 'Selamat datang di profil resmi ' . $tenant->name . '. Lembaga kami berkomitmen memberikan layanan terbaik bagi masyarakat.' }}
                </p>
                
                @if($tenant->address)
                    <div class="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-sm border border-white inline-block text-left">
                        <div class="flex items-start space-x-3">
                            <svg class="h-6 w-6 text-indigo-600 mt-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <div>
                                <h3 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-1">Alamat</h3>
                                <p class="text-gray-600 italic">{{ $tenant->address }}</p>
                            </div>
                        </div>
                    </div>
                @endif
            </div>

            <div class="mt-12 flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
                <a href="https://wa.me/{{ preg_replace('/[^0-9]/', '', $tenant->whatsapp_number) }}" target="_blank" class="px-8 py-4 bg-green-500 text-white rounded-full font-bold shadow-lg hover:bg-green-600 transition flex items-center justify-center space-x-2">
                    <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                    </svg>
                    <span>Hubungi Kami</span>
                </a>
                <a href="/" class="px-8 py-4 bg-white text-gray-700 border border-gray-200 rounded-full font-bold shadow-sm hover:bg-gray-50 transition">
                    Kembali ke Beranda
                </a>
            </div>
        </div>
    </div>

    <!-- Additional Content (Placeholder) -->
    <div class="bg-white py-24">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
                <div class="p-8 rounded-3xl bg-gray-50 hover:bg-white hover:shadow-2xl transition duration-300">
                    <div class="h-16 w-16 bg-indigo-100 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                        <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 mb-4">Visi & Misi</h3>
                    <p class="text-gray-500">Mewujudkan ekosistem pendidikan yang unggul dan mandiri melalui inovasi tanpa henti.</p>
                </div>
                <div class="p-8 rounded-3xl bg-indigo-600 text-white shadow-2xl transform scale-105">
                    <div class="h-16 w-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                        <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-4">Layanan Unggulan</h3>
                    <p class="text-white/80">Program pendidikan dan pembinaan karakter berbasis nilai-nilai luhur pondok.</p>
                </div>
                <div class="p-8 rounded-3xl bg-gray-50 hover:bg-white hover:shadow-2xl transition duration-300">
                    <div class="h-16 w-16 bg-pink-100 text-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                        <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 mb-4">Komunitas Kami</h3>
                    <p class="text-gray-500">Bergabunglah dengan ribuan santri dan pendidik yang telah bersama kami.</p>
                </div>
            </div>
        </div>
    </div>
</x-guest-layout>
