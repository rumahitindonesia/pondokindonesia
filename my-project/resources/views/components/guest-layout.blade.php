<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="csrf-token" content="{{ csrf_token() }}">

        @stack('seo')

        <title>{{ $title ?? 'Pondok Indonesia' }}</title>

        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            indigo: { 50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe', 300: '#a5b4fc', 400: '#818cf8', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca', 800: '#3730a3', 900: '#312e81', 950: '#1e1b4b' },
                        },
                        fontFamily: { sans: ['Inter', 'sans-serif'] },
                    }
                }
            }
        </script>
    </head>
    <body class="font-sans text-gray-900 antialiased bg-white">
        <div class="min-h-screen">
            @if(view()->exists('layouts.navigation-guest'))
                @include('layouts.navigation-guest')
            @endif

            <main>
                {{ $slot }}
            </main>

            @if(view()->exists('layouts.footer-guest'))
                @include('layouts.footer-guest')
            @endif
        </div>
    </body>
</html>
