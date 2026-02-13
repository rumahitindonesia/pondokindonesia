<?php

namespace App\Filament\Central\Resources;

use App\Filament\Central\Resources\SystemLogResource\Pages;
use App\Models\SystemLog;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class SystemLogResource extends Resource
{
    protected static ?string $model = SystemLog::class;

    protected static ?string $navigationIcon = 'heroicon-o-exclamation-circle';

    protected static ?string $navigationGroup = 'System';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Error Details')
                    ->schema([
                        Forms\Components\TextInput::make('level'),
                        Forms\Components\TextInput::make('exception'),
                        Forms\Components\Textarea::make('message')
                            ->columnSpanFull(),
                        Forms\Components\Textarea::make('trace')
                            ->columnSpanFull()
                            ->rows(10),
                    ])->columns(2),
                Forms\Components\Section::make('Request Info')
                    ->schema([
                        Forms\Components\TextInput::make('url'),
                        Forms\Components\TextInput::make('method'),
                        Forms\Components\TextInput::make('ip'),
                        Forms\Components\TextInput::make('user_id'),
                        Forms\Components\Textarea::make('user_agent')
                            ->columnSpanFull(),
                    ])->columns(3),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->label('Time'),
                Tables\Columns\TextColumn::make('level')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'error' => 'danger',
                        'warning' => 'warning',
                        'info' => 'info',
                        default => 'gray',
                    }),
                Tables\Columns\TextColumn::make('message')
                    ->limit(50)
                    ->searchable(),
                Tables\Columns\TextColumn::make('url')
                    ->limit(30),
                Tables\Columns\TextColumn::make('ip'),
            ])
            ->defaultSort('created_at', 'desc')
            ->filters([
                Tables\Filters\SelectFilter::make('level')
                    ->options([
                        'error' => 'Error',
                        'warning' => 'Warning',
                        'info' => 'Info',
                    ]),
            ])
            ->actions([
                Tables\Actions\ViewAction::make(),
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
            'index' => Pages\ListSystemLogs::route('/'),
            'view' => Pages\ViewSystemLog::route('/{record}'),
        ];
    }
}
