<?php

namespace App\Filament\Resources;

use App\Filament\Resources\LeadResource\Pages;
use App\Models\Lead;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;

class LeadResource extends Resource
{
    protected static ?string $model = Lead::class;

    protected static ?string $navigationIcon = 'heroicon-o-user-group';

    protected static ?string $navigationGroup = 'PPDB Online';

    protected static ?string $tenantOwnershipRelationshipName = 'tenant'; // Lead usually belongs to Tenant through Campaign or has tenant_id

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Basic Info')
                    ->schema([
                        Forms\Components\Select::make('campaign_id')
                            ->relationship('campaign', 'title')
                            ->searchable()
                            ->preload(),
                        Forms\Components\TextInput::make('name')
                            ->required(),
                        Forms\Components\TextInput::make('email')
                            ->email(),
                        Forms\Components\TextInput::make('whatsapp')
                            ->required(),
                        Forms\Components\TextInput::make('status')
                            ->disabled()
                            ->dehydrated(false),
                    ])->columns(2),

                Forms\Components\Section::make('Workflow Status')
                    ->schema([
                        Forms\Components\Select::make('status')
                            ->options([
                                'new' => 'New',
                                'contacted' => 'Contacted',
                                'closing' => 'Closing',
                                'registered' => 'Registered',
                                'interviewed' => 'Interviewed',
                                'accepted' => 'Accepted',
                                'rejected' => 'Rejected',
                                'santri' => 'Santri',
                            ])
                            ->required()
                            ->native(false),
                    ]),

                Forms\Components\Section::make('Payment Info')
                    ->schema([
                        Forms\Components\Select::make('payment_status')
                            ->options([
                                'unpaid' => 'Unpaid',
                                'partial' => 'Partial',
                                'paid' => 'Paid',
                            ]),
                        Forms\Components\TextInput::make('total_amount')
                            ->numeric()
                            ->prefix('IDR'),
                        Forms\Components\TextInput::make('paid_amount')
                            ->numeric()
                            ->prefix('IDR')
                            ->disabled(),
                        Forms\Components\TextInput::make('remaining_amount')
                            ->numeric()
                            ->prefix('IDR')
                            ->disabled(),
                    ])->columns(2),

                Forms\Components\Section::make('Interview Info')
                    ->schema([
                        Forms\Components\DateTimePicker::make('interview_date'),
                        Forms\Components\Select::make('interview_status')
                            ->options([
                                'scheduled' => 'Scheduled',
                                'completed' => 'Completed',
                                'passed' => 'Passed',
                                'failed' => 'Failed',
                            ]),
                    ])->columns(2),

                Forms\Components\Section::make('Registration Data')
                    ->schema([
                        Forms\Components\KeyValue::make('registration_data'),
                    ])->columnSpanFull(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('whatsapp')
                    ->searchable(),
                Tables\Columns\BadgeColumn::make('status')
                    ->color(fn (string $state): string => match ($state) {
                        'new' => 'gray',
                        'contacted' => 'warning',
                        'closing' => 'primary',
                        'registered' => 'info',
                        'interviewed' => 'info',
                        'accepted' => 'success',
                        'rejected' => 'danger',
                        'santri' => 'success',
                    }),
                Tables\Columns\TextColumn::make('payment_status')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'unpaid' => 'danger',
                        'partial' => 'warning',
                        'paid' => 'success',
                        default => 'gray',
                    }),
                Tables\Columns\TextColumn::make('campaign.title')
                    ->sortable(),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        'new' => 'New',
                        'contacted' => 'Contacted',
                        'closing' => 'Closing',
                        'registered' => 'Registered',
                        'accepted' => 'Accepted',
                        'santri' => 'Santri',
                    ]),
                Tables\Filters\SelectFilter::make('campaign_id')
                    ->relationship('campaign', 'title'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\ActionGroup::make([
                    Tables\Actions\Action::make('convert_to_santri')
                        ->icon('heroicon-o-academic-cap')
                        ->color('success')
                        ->label('Jadi Santri')
                        ->requiresConfirmation()
                        ->action(fn (Lead $record) => $record->convertToSantri())
                        ->visible(fn (Lead $record) => $record->status === 'accepted' && $record->campaign->type === 'ppdb'),
                    
                    Tables\Actions\Action::make('convert_to_donor')
                        ->icon('heroicon-o-heart')
                        ->color('success')
                        ->label('Jadi Donatur')
                        ->requiresConfirmation()
                        ->action(fn (Lead $record) => $record->convertToDonor())
                        ->visible(fn (Lead $record) => $record->status === 'accepted' && $record->campaign->type === 'fundraising'),
                    
                    Tables\Actions\Action::make('send_reminder')
                        ->icon('heroicon-o-chat-bubble-left-right')
                        ->color('warning')
                        ->action(fn (Lead $record) => $record->sendPaymentReminder())
                        ->visible(fn (Lead $record) => in_array($record->payment_status, ['unpaid', 'partial'])),
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

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListLeads::route('/'),
            'create' => Pages\CreateLead::route('/create'),
            'edit' => Pages\EditLead::route('/{record}/edit'),
        ];
    }
}
