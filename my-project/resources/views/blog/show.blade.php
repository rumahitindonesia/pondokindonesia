<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{{ $post->title }} - {{ config('app.name', 'Laravel') }}</title>
        <!-- Fonts -->
        <link rel="preconnect" href="https://fonts.bunny.net">
        <link href="https://fonts.bunny.net/css?family=instrument-sans:400,500,600,700" rel="stylesheet" />
        <!-- Styles / Scripts -->
        @if (file_exists(public_path('build/manifest.json')) || file_exists(public_path('hot')))
            @vite(['resources/css/app.css', 'resources/js/app.js'])
        @else
            <script src="https://cdn.tailwindcss.com"></script>
        @endif
        <style>
            .prose h2 { font-size: 1.5rem; font-weight: 700; margin-top: 2rem; margin-bottom: 1rem; }
            .prose h3 { font-size: 1.25rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.75rem; }
            .prose p { margin-bottom: 1.25rem; line-height: 1.75; }
            .prose ul { list-style-type: disc; padding-left: 1.5rem; margin-bottom: 1.25rem; }
            .prose ol { list-style-type: decimal; padding-left: 1.5rem; margin-bottom: 1.25rem; }
            .prose blockquote { border-left-width: 4px; padding-left: 1rem; font-style: italic; color: #4b5563; margin-bottom: 1.25rem; }
            .dark .prose blockquote { color: #d1d5db; }
        </style>
    </head>
    <body class="bg-[#FDFDFC] dark:bg-[#0a0a0a] text-[#1b1b18] dark:text-[#EDEDEC] min-h-screen font-sans antialiased">
        
        <!-- Navigation -->
        <header class="w-full max-w-4xl mx-auto px-6 py-6 flex justify-between items-center">
            <a href="{{ url('/') }}" class="text-xl font-bold">
                {{ config('app.name', 'Laravel') }}
            </a>
            <nav class="flex items-center gap-4 text-sm font-medium">
                <a href="{{ url('/') }}" class="hover:underline">Home</a>
                <a href="{{ route('blog.index') }}" class="hover:underline font-bold">Blog</a>
            </nav>
        </header>

        <!-- Main Content -->
        <article class="max-w-3xl mx-auto px-6 py-12">
            <header class="mb-8 text-center">
                <div class="text-sm text-gray-500 dark:text-gray-400 mb-2">
                    {{ $post->published_at ? $post->published_at->format('F d, Y') : 'Draft' }}
                </div>
                <h1 class="text-3xl md:text-5xl font-bold mb-6 leading-tight">{{ $post->title }}</h1>
            </header>

            @if($post->image)
                <div class="mb-10 rounded-xl overflow-hidden shadow-lg">
                    <img src="{{ Storage::url($post->image) }}" alt="{{ $post->title }}" class="w-full h-auto object-cover">
                </div>
            @endif

            <div class="prose max-w-none text-lg text-gray-800 dark:text-gray-200">
                {!! $post->content !!}
            </div>

            <div class="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800">
                <a href="{{ route('blog.index') }}" class="inline-flex items-center text-amber-600 hover:text-amber-700 font-medium">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                    Back to Blog
                </a>
            </div>
        </article>

        <!-- Footer -->
        <footer class="border-t border-gray-200 dark:border-gray-800 mt-20 py-12">
            <div class="max-w-7xl mx-auto px-6 text-center text-gray-500 dark:text-gray-400 text-sm">
                &copy; {{ date('Y') }} {{ config('app.name', 'Laravel') }}. All rights reserved.
            </div>
        </footer>
    </body>
</html>
