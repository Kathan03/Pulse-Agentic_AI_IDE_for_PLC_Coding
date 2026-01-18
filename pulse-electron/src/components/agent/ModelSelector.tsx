/**
 * ModelSelector - Quick Model Change in Chat Header
 *
 * Allows changing the master agent model directly from chat window.
 */

import { useState, useEffect } from 'react';
import { fetchSettings, updateModel } from '@/services/settingsApi';

// Available models - must match SettingsTab and llm_client.py
const AVAILABLE_MODELS = [
    // GPT-5 series
    'gpt-5.2', 'gpt-5.1', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano',
    'gpt-5.2-codex', 'gpt-5.1-codex-max', 'gpt-5.1-codex',
    'gpt-5.2-pro', 'gpt-5-pro',
    // Claude 4.5 series
    'claude-sonnet-4.5', 'claude-opus-4.5',
    // Gemini 3 series
    'gemini-3-pro', 'gemini-3-flash'
];

export function ModelSelector() {
    const [currentModel, setCurrentModel] = useState('gpt-5');
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Load current model on mount
    useEffect(() => {
        async function loadModel() {
            try {
                const settings = await fetchSettings();
                setCurrentModel(settings.models.master_agent || 'gpt-5');
            } catch (error) {
                console.error('Failed to load model:', error);
            } finally {
                setIsLoading(false);
            }
        }
        loadModel();
    }, []);

    const handleModelChange = async (model: string) => {
        try {
            await updateModel('master_agent', model);
            setCurrentModel(model);
            setIsOpen(false);
        } catch (error) {
            console.error('Failed to update model:', error);
        }
    };

    // Get display name (shortened for UI)
    const getDisplayName = (model: string) => {
        if (model.startsWith('gpt-5')) return model.replace('gpt-', 'GPT-');
        if (model.startsWith('claude')) return model.replace('claude-', 'Claude ').replace('-4.5', ' 4.5');
        if (model.startsWith('gemini')) return model.replace('gemini-', 'Gemini ').replace('-', ' ');
        return model;
    };

    if (isLoading) {
        return (
            <div className="px-2 py-1 text-xs text-pulse-fg-muted">
                Loading...
            </div>
        );
    }

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-1.5 px-2 py-1 text-xs rounded hover:bg-pulse-bg-tertiary transition-colors"
                title="Change Model"
            >
                <ModelIcon />
                <span className="text-pulse-fg-muted">{getDisplayName(currentModel)}</span>
                <ChevronIcon isOpen={isOpen} />
            </button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Dropdown */}
                    <div className="absolute right-0 top-full mt-1 z-50 min-w-48 bg-pulse-bg-secondary border border-pulse-border rounded-lg shadow-lg overflow-hidden">
                        <div className="p-1 max-h-64 overflow-auto">
                            {/* GPT-5 Group */}
                            <div className="px-2 py-1 text-xs font-semibold text-pulse-fg-muted uppercase tracking-wide">
                                OpenAI
                            </div>
                            {AVAILABLE_MODELS.filter(m => m.startsWith('gpt')).map(model => (
                                <ModelOption
                                    key={model}
                                    displayName={getDisplayName(model)}
                                    isSelected={model === currentModel}
                                    onClick={() => handleModelChange(model)}
                                />
                            ))}

                            {/* Claude Group */}
                            <div className="px-2 py-1 mt-1 text-xs font-semibold text-pulse-fg-muted uppercase tracking-wide">
                                Anthropic
                            </div>
                            {AVAILABLE_MODELS.filter(m => m.startsWith('claude')).map(model => (
                                <ModelOption
                                    key={model}
                                    displayName={getDisplayName(model)}
                                    isSelected={model === currentModel}
                                    onClick={() => handleModelChange(model)}
                                />
                            ))}

                            {/* Gemini Group */}
                            <div className="px-2 py-1 mt-1 text-xs font-semibold text-pulse-fg-muted uppercase tracking-wide">
                                Google
                            </div>
                            {AVAILABLE_MODELS.filter(m => m.startsWith('gemini')).map(model => (
                                <ModelOption
                                    key={model}
                                    displayName={getDisplayName(model)}
                                    isSelected={model === currentModel}
                                    onClick={() => handleModelChange(model)}
                                />
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function ModelOption({
    displayName,
    isSelected,
    onClick,
}: {
    displayName: string;
    isSelected: boolean;
    onClick: () => void;
}) {
    return (
        <button
            onClick={onClick}
            className={`w-full px-2 py-1.5 text-left text-xs rounded flex items-center justify-between ${isSelected
                ? 'bg-pulse-primary/20 text-pulse-primary'
                : 'text-pulse-fg hover:bg-pulse-bg-tertiary'
                }`}
        >
            <span>{displayName}</span>
            {isSelected && <CheckIcon />}
        </button>
    );
}

function ModelIcon() {
    return (
        <svg viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5 text-pulse-primary">
            <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 1a6 6 0 110 12A6 6 0 018 2zm0 2a4 4 0 100 8 4 4 0 000-8zm0 1a3 3 0 110 6 3 3 0 010-6z" />
        </svg>
    );
}

function ChevronIcon({ isOpen }: { isOpen: boolean }) {
    return (
        <svg
            viewBox="0 0 16 16"
            fill="currentColor"
            className={`w-3 h-3 text-pulse-fg-muted transition-transform ${isOpen ? 'rotate-180' : ''}`}
        >
            <path d="M4 6l4 4 4-4H4z" />
        </svg>
    );
}

function CheckIcon() {
    return (
        <svg viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3">
            <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" />
        </svg>
    );
}
