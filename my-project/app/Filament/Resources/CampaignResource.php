<?php

namespace App\Filament\Resources;

use App\Filament\Resources\CampaignResource\Pages;
use App\Models\Campaign;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Filament\Facades\Filament;
use Illuminate\Support\Str;

class CampaignResource extends Resource
{
    protected static ?string $model = Campaign::class;

    protected static ?string $navigationIcon = 'heroicon-o-megaphone';

    protected static ?string $navigationGroup = 'PPDB Online';

    protected static ?string $tenantOwnershipRelationshipName = 'tenant';

    protected static ?string $tenantRelationshipName = 'campaigns';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Campaign Details')
                    ->schema([
                        Forms\Components\Select::make('type')
                            ->options([
                                'ppdb' => 'PPDB',
                                'fundraising' => 'Fundraising',
                            ])
                            ->required()
                            ->default('ppdb')
                            ->live(),
                        Forms\Components\TextInput::make('title')
                            ->required()
                            ->live(onBlur: true)
                            ->afterStateUpdated(fn (Forms\Set $set, ?string $state) => $set('slug', Str::slug($state))),
                        Forms\Components\TextInput::make('slug')
                            ->required()
                            ->unique(Campaign::class, 'slug', ignoreRecord: true),
                        Forms\Components\FileUpload::make('image')
                            ->image()
                            ->columnSpanFull(),
                        
                        // PPDB Only
                        Forms\Components\Grid::make(2)
                            ->visible(fn (Forms\Get $get) => $get('type') === 'ppdb')
                            ->schema([
                                Forms\Components\TextInput::make('registration_fee')
                                    ->numeric()
                                    ->prefix('IDR')
                                    ->default(0)
                                    ->required(),
                                Forms\Components\TextInput::make('education_fee')
                                    ->numeric()
                                    ->prefix('IDR')
                                    ->default(0)
                                    ->required(),
                            ]),

                        // Fundraising Only
                        Forms\Components\Grid::make(1)
                            ->visible(fn (Forms\Get $get) => $get('type') === 'fundraising')
                            ->schema([
                                Forms\Components\TextInput::make('target_amount')
                                    ->numeric()
                                    ->prefix('IDR')
                                    ->default(0)
                                    ->required(),
                            ]),

                        Forms\Components\Grid::make(3)
                            ->schema([
                                Forms\Components\TextInput::make('aff_id')
                                    ->label('Affiliate code (optional)')
                                    ->hint('Default affiliate code for this campaign'),
                                Forms\Components\DatePicker::make('start_date'),
                                Forms\Components\DatePicker::make('end_date'),
                            ]),

                        Forms\Components\Grid::make(2)
                            ->schema([
                                Forms\Components\Toggle::make('is_active')
                                    ->default(true)
                                    ->label('Campaign Active'),
                                Forms\Components\Select::make('status')
                                    ->options([
                                        'draft' => 'Draft',
                                        'active' => 'Active',
                                        'completed' => 'Completed',
                                    ])
                                    ->default('active')
                                    ->required(),
                            ]),
                    ]),
                
                Forms\Components\Section::make('Landing Page Content')
                    ->schema([
                        Forms\Components\RichEditor::make('landing_page_content')
                            ->label('Content HTML')
                            ->columnSpanFull()
                            ->hintAction(
                                Forms\Components\Actions\Action::make('generateAI')
                                    ->label('Generate with AI')
                                    ->icon('heroicon-o-sparkles')
                                    ->action(function (Forms\Get $get, Forms\Set $set) {
                                        $title = $get('title');
                                        $description = $get('description');
                                        
                                        if (!$title) {
                                            \Filament\Notifications\Notification::make()
                                                ->title('Please enter a campaign title first')
                                                ->warning()
                                                ->send();
                                            return;
                                        }

                                        $service = new \App\Services\GroqService();
                                        $result = $service->generatePPDBLandingPage($title, $description ?? '');

                                        if ($result) {
                                            $html = "<h1>{$result['headline']}</h1>";
                                            $html .= "<p class='lead'>{$result['subheadline']}</p>";
                                            $html .= $result['content_html'];
                                            
                                            $set('landing_page_content', $html);
                                            
                                            \Filament\Notifications\Notification::make()
                                                ->title('Landing page content generated')
                                                ->success()
                                                ->send();
                                        }
                                    })
                            ),
                    ]),
                
                Forms\Components\Section::make('SEO Optimization')
                    ->schema([
                        Forms\Components\TextInput::make('meta_title')
                            ->placeholder('Judul SEO (kosongkan untuk default dari Title)'),
                        Forms\Components\Textarea::make('meta_description')
                            ->rows(3)
                            ->placeholder('Deskripsi SEO untuk Google...'),
                        Forms\Components\TextInput::make('seo_keywords')
                            ->placeholder('kata kunci, terpisah, koma'),
                    ])
                    ->collapsed(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('type')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'ppdb' => 'success',
                        'fundraising' => 'warning',
                    }),
                Tables\Columns\TextColumn::make('title')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('public_url')
                    ->label('Landing Page')
                    ->getStateUsing(fn ($record) => route('campaign.show', [$record->tenant->slug, $record->slug]))
                    ->copyable()
                    ->color('primary')
                    ->icon('heroicon-o-link')
                    ->tooltip('Klik untuk salin link')
                    ->limit(20),
                Tables\Columns\TextColumn::make('registration_fee')
                    ->label('Reg Fee')
                    ->money('IDR')
                    ->visible(fn ($record) => $record?->type === 'ppdb')
                    ->sortable(),
                Tables\Columns\TextColumn::make('target_amount')
                    ->label('Target')
                    ->money('IDR')
                    ->visible(fn ($record) => $record?->type === 'fundraising')
                    ->sortable(),
                Tables\Columns\IconColumn::make('is_active')
                    ->boolean(),
                Tables\Columns\TextColumn::make('status')
                    ->badge(),
                Tables\Columns\TextColumn::make('leads_count')
                    ->counts('leads')
                    ->label('Total Leads'),
                Tables\Columns\TextColumn::make('start_date')
                    ->date()
                    ->sortable(),
                Tables\Columns\TextColumn::make('end_date')
                    ->date()
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\TernaryFilter::make('is_active'),
            ])
            ->actions([
                Tables\Actions\ActionGroup::make([
                    Tables\Actions\EditAction::make(),
                    Tables\Actions\Action::make('share_wa')
                        ->label('Bagikan ke WA')
                        ->icon('heroicon-o-chat-bubble-left-right')
                        ->color('success')
                        ->url(fn ($record) => "https://wa.me/?text=" . urlencode("Yuk cek " . $record->title . " di sini: " . route('campaign.show', [$record->tenant->slug, $record->slug])))
                        ->openUrlInNewTab(),
                    Tables\Actions\DeleteAction::make(),
                ]),
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

    public static function getWidgets(): array
    {
        return [
            \App\Filament\Resources\CampaignResource\Widgets\CampaignAnalytics::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListCampaigns::route('/'),
            'create' => Pages\CreateCampaign::route('/create'),
            'edit' => Pages\EditCampaign::route('/{record}/edit'),
        ];
    }
}
