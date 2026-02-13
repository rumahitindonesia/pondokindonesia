<?php

namespace App\Filament\Resources;

use App\Filament\Resources\CrmInvoiceResource\Pages;
use App\Models\CrmInvoice;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class CrmInvoiceResource extends Resource
{
    protected static ?string $model = CrmInvoice::class;

    protected static ?string $navigationIcon = 'heroicon-o-document-text';

    protected static ?string $navigationGroup = 'CRM';

    protected static ?string $pluralLabel = 'Invoices';

    protected static ?string $singularLabel = 'Invoice';

    protected static ?string $tenantOwnershipRelationshipName = 'tenant';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make()
                    ->schema([
                        Forms\Components\Select::make('type')
                            ->options([
                                'spp' => 'SPP',
                                'recurring_donation' => 'Recurring Donation',
                                'one_time_donation' => 'One-time Donation',
                            ])
                            ->required()
                            ->live(),
                        Forms\Components\Select::make('santri_id')
                            ->relationship('santri', 'name')
                            ->visible(fn (Forms\Get $get) => $get('type') === 'spp')
                            ->required(fn (Forms\Get $get) => $get('type') === 'spp'),
                        Forms\Components\Select::make('donor_id')
                            ->relationship('donor', 'name')
                            ->visible(fn (Forms\Get $get) => in_array($get('type'), ['recurring_donation', 'one_time_donation']))
                            ->required(fn (Forms\Get $get) => in_array($get('type'), ['recurring_donation', 'one_time_donation'])),
                        Forms\Components\TextInput::make('amount')
                            ->numeric()
                            ->prefix('IDR')
                            ->required(),
                        Forms\Components\DatePicker::make('due_date')
                            ->required(),
                        Forms\Components\TextInput::make('period')
                            ->placeholder('e.g. 2026-02'),
                        Forms\Components\Select::make('status')
                            ->options([
                                'pending' => 'Pending',
                                'paid' => 'Paid',
                                'cancelled' => 'Cancelled',
                            ])
                            ->default('pending')
                            ->required(),
                        Forms\Components\DateTimePicker::make('paid_at'),
                    ])->columns(2),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('type')
                    ->badge(),
                Tables\Columns\TextColumn::make('santri.name')
                    ->label('Santri/Donor')
                    ->formatStateUsing(fn ($record) => $record->santri ? $record->santri->name : ($record->donor ? $record->donor->name : '-'))
                    ->searchable(),
                Tables\Columns\TextColumn::make('amount')
                    ->money('IDR')
                    ->sortable(),
                Tables\Columns\TextColumn::make('due_date')
                    ->date()
                    ->sortable(),
                Tables\Columns\BadgeColumn::make('status')
                    ->color(fn (string $state): string => match ($state) {
                        'paid' => 'success',
                        'pending' => 'warning',
                        'cancelled' => 'danger',
                    }),
                Tables\Columns\TextColumn::make('period'),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'paid' => 'Paid',
                        'cancelled' => 'Cancelled',
                    ]),
                Tables\Filters\SelectFilter::make('type')
                    ->options([
                        'spp' => 'SPP',
                        'recurring_donation' => 'Recurring Donation',
                    ]),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\Action::make('send_reminder')
                    ->label('Send WA')
                    ->icon('heroicon-o-chat-bubble-left-right')
                    ->color('warning')
                    ->hidden(fn (CrmInvoice $record) => $record->status === 'paid')
                    ->action(function (CrmInvoice $record) {
                        $tenant = $record->tenant;
                        $service = new \App\Services\StarSenderService($tenant);
                        
                        if ($record->type === 'spp' && $record->santri) {
                            $service->sendSPPReminder($record);
                        } elseif ($record->donor) {
                            $service->sendDonorReminder($record);
                        }

                        \Filament\Notifications\Notification::make()
                            ->title('WhatsApp notification sent')
                            ->success()
                            ->send();
                    }),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListCrmInvoices::route('/'),
            'create' => Pages\CreateCrmInvoice::route('/create'),
            'edit' => Pages\EditCrmInvoice::route('/{record}/edit'),
        ];
    }
}
