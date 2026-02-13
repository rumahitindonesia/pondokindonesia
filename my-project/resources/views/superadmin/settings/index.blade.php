<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 leading-tight">
            {{ __('Settings') }}
        </h2>
    </x-slot>

    <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                <div class="p-6 text-gray-900">
                    @if (session('success'))
                        <div class="mb-4 font-medium text-sm text-green-600">
                            {{ session('success') }}
                        </div>
                    @endif

                    <form method="POST" action="{{ route('superadmin.settings.update') }}">
                        @csrf
                        @method('PUT')

                        <div>
                            <x-input-label for="starsender_api_key" :value="__('StarSender API Key')" />
                            <x-text-input id="starsender_api_key" class="block mt-1 w-full" type="text" name="starsender_api_key" :value="old('starsender_api_key', $starsender_api_key)" required autofocus />
                            <x-input-error :messages="$errors->get('starsender_api_key')" class="mt-2" />
                        </div>

                        <div class="flex items-center justify-end mt-4">
                            <x-primary-button class="ml-4">
                                {{ __('Save Settings') }}
                            </x-primary-button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</x-app-layout>
