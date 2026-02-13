<?php

namespace App\Filament\Central\Pages;

use App\Models\Setting;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Pages\Page;

class Settings extends Page implements HasForms
{
    protected static ?string $slug = 'app-settings';

    use InteractsWithForms;

    protected static ?string $navigationIcon = 'heroicon-o-cog-6-tooth';

    protected static string $view = 'filament.central.pages.settings';

    protected static ?string $navigationLabel = 'Settings';

    protected static ?string $title = 'Application Settings';

    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill([
            'starsender_api_key' => Setting::get('starsender_api_key'),
            'gemini_api_key' => Setting::get('gemini_api_key'),
            'groq_api_key' => Setting::get('groq_api_key'),
        ]);
    }

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                \Filament\Forms\Components\Section::make('StarSender API')
                    ->description('Configuration for WhatsApp OTP and Notifications via StarSender.')
                    ->schema([
                        TextInput::make('starsender_api_key')
                            ->label('API Key')
                            ->password()
                            ->revealable()
                            ->required(),
                    ]),

                \Filament\Forms\Components\Section::make('Gemini AI API')
                    ->description('Configuration for AI Content Generation via Google Gemini.')
                    ->collapsible()
                    ->collapsed() // Clean up UI as we are switching to Groq
                    ->schema([
                        TextInput::make('gemini_api_key')
                            ->label('API Key')
                            ->password()
                            ->revealable()
                            ->helperText('Get your API key from Google AI Studio.'),
                    ]),

                \Filament\Forms\Components\Section::make('Groq AI API')
                    ->description('Configuration for AI Content Generation via Groq (Llama 3).')
                    ->schema([
                        TextInput::make('groq_api_key')
                            ->label('API Key')
                            ->password()
                            ->revealable()
                            ->helperText('Get your free API key from console.groq.com.'),
                    ]),
            ])
            ->statePath('data');
    }

    public function save(): void
    {
        $data = $this->form->getState();

        Setting::set('starsender_api_key', $data['starsender_api_key']);
        Setting::set('gemini_api_key', $data['gemini_api_key'] ?? null);
        Setting::set('groq_api_key', $data['groq_api_key'] ?? null);

        Notification::make()
            ->success()
            ->title('Settings saved successfully')
            ->send();
    }
}
