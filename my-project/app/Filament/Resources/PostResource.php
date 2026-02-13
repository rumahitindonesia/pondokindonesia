<?php

namespace App\Filament\Resources;

use App\Filament\Resources\PostResource\Pages;
use App\Filament\Resources\PostResource\RelationManagers;
use App\Models\Post;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;

class PostResource extends Resource
{
    protected static ?string $model = Post::class;

    protected static ?string $navigationIcon = 'heroicon-o-rectangle-stack';

    protected static ?string $tenantOwnershipRelationshipName = 'tenant';

    protected static ?string $tenantRelationshipName = 'posts';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make()
                    ->schema([
                        Forms\Components\TextInput::make('title')
                            ->required()
                            ->live(onBlur: true)
                            ->afterStateUpdated(fn (Forms\Set $set, ?string $state) => $set('slug', \Illuminate\Support\Str::slug($state))),
                        Forms\Components\TextInput::make('slug')
                            ->required()
                            ->unique(ignoreRecord: true),
                        Forms\Components\FileUpload::make('image')
                            ->image()
                            ->directory('blog'),
                        Forms\Components\RichEditor::make('content')
                            ->required()
                            ->columnSpanFull()
                            ->hintAction(
                                Forms\Components\Actions\Action::make('generateAI')
                                    ->label('Generate with AI')
                                    ->icon('heroicon-o-sparkles')
                                    ->form([
                                        Forms\Components\TextInput::make('prompt')
                                            ->label('What should the blog post be about?')
                                            ->placeholder('e.g. Tips for learning Laravel in 2026')
                                            ->required(),
                                    ])
                                    ->action(function (array $data, Forms\Set $set) {
                                        $service = new \App\Services\GroqService();
                                        $result = $service->generatePostContent($data['prompt']);

                                        if ($result) {
                                            $set('title', $result['title']);
                                            $set('slug', \Illuminate\Support\Str::slug($result['title']));
                                            $set('content', $result['content']);
                                            $set('meta_title', $result['meta_title'] ?? null);
                                            $set('meta_description', $result['meta_description'] ?? null);
                                            $set('meta_keywords', $result['meta_keywords'] ?? null);
                                            
                                            \Filament\Notifications\Notification::make()
                                                ->title('Content Generated via Groq')
                                                ->success()
                                                ->send();
                                        } else {
                                            \Filament\Notifications\Notification::make()
                                                ->title('Failed to generate content')
                                                ->body('Check logs for details or ensure API key is valid.')
                                                ->danger()
                                                ->send();
                                        }
                                    })
                            ),
                        Forms\Components\Toggle::make('is_published')
                            ->live()
                            ->afterStateUpdated(function (Forms\Get $get, Forms\Set $set, ?bool $state) {
                                if ($state && !$get('published_at')) {
                                    $set('published_at', now()->toDateTimeString());
                                }
                            }),
                        Forms\Components\DateTimePicker::make('published_at')
                            ->hidden(fn (Forms\Get $get) => !$get('is_published'))
                            ->required(fn (Forms\Get $get) => $get('is_published')),
                    ])->columns(2),
            Forms\Components\Section::make('SEO Settings')
                ->schema([
                    Forms\Components\TextInput::make('meta_title')
                        ->label('Meta Title')
                        ->maxLength(60),
                    Forms\Components\Textarea::make('meta_description')
                        ->label('Meta Description')
                        ->maxLength(160),
                    Forms\Components\TextInput::make('meta_keywords')
                        ->label('Meta Keywords')
                        ->placeholder('keyword1, keyword2, keyword3'),
                ])->collapsible(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\ImageColumn::make('image'),
                Tables\Columns\TextColumn::make('title')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\IconColumn::make('is_published')
                    ->boolean()
                    ->label('Published'),
                Tables\Columns\TextColumn::make('published_at')
                    ->dateTime()
                    ->sortable(),
                Tables\Columns\TextColumn::make('user.name')
                    ->label('Author')
                    ->sortable(),
            ])
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListPosts::route('/'),
            'create' => Pages\CreatePost::route('/create'),
            'edit' => Pages\EditPost::route('/{record}/edit'),
        ];
    }
}
