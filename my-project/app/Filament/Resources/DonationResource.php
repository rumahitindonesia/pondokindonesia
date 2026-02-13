<?php

namespace App\Filament\Resources;

use App\Filament\Resources\DonationResource\Pages;
use App\Models\Donation;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;

class DonationResource extends Resource
{
    protected static ?string $model = Donation::class;

    protected static ?string $navigationIcon = 'heroicon-o-heart';

    protected static ?string $navigationGroup = 'Fundraising';

    protected static ?string $tenantOwnershipRelationshipName = 'tenant';

    protected static ?string $tenantRelationshipName = 'donations';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make()
                    ->schema([
                        Forms\Components\Select::make('campaign_id')
                            ->relationship('campaign', 'title')
                            ->required(),
                        Forms\Components\TextInput::make('donor_name')
                            ->required(),
                        Forms\Components\TextInput::make('amount')
                            ->numeric()
                            ->prefix('IDR')
                            ->required(),
                        Forms\Components\TextInput::make('wa_number')
                            ->label('WhatsApp Number')
                            ->tel(),
                        Forms\Components\Select::make('status')
                            ->options([
                                'pending' => 'Pending',
                                'success' => 'Success',
                                'failed' => 'Failed',
                            ])
                            ->default('pending')
                            ->required(),
                        Forms\Components\Textarea::make('message')
                            ->columnSpanFull(),
                    ])->columns(2),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Date')
                    ->dateTime()
                    ->sortable(),
                Tables\Columns\TextColumn::make('campaign.title')
                    ->label('Campaign')
                    ->searchable(),
                Tables\Columns\TextColumn::make('donor_name')
                    ->searchable(),
                Tables\Columns\TextColumn::make('amount')
                    ->money('IDR')
                    ->sortable(),
                Tables\Columns\BadgeColumn::make('status')
                    ->color(fn (string $state): string => match ($state) {
                        'success' => 'success',
                        'pending' => 'warning',
                        'failed' => 'danger',
                    }),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('campaign')
                    ->relationship('campaign', 'title'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\Action::make('confirmDonation')
                    ->label('Confirm & Notify')
                    ->icon('heroicon-o-check-circle')
                    ->color('success')
                    ->hidden(fn (Donation $record) => $record->status === 'success')
                    ->action(function (Donation $record) {
                        $record->update(['status' => 'success']);

                        \Filament\Notifications\Notification::make()
                            ->title('Donation Confirmed & Notification Sent')
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

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListDonations::route('/'),
            'create' => Pages\CreateDonation::route('/create'),
            'edit' => Pages\EditDonation::route('/{record}/edit'),
        ];
    }
}
