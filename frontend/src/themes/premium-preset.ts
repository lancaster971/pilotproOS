import { definePreset } from '@primevue/themes';

const PremiumPreset = definePreset({
    semantic: {
        primary: {
            50: '{green.50}',
            100: '{green.100}',
            200: '{green.200}',
            300: '{green.300}',
            400: '{green.400}',
            500: '{green.500}',
            600: '{green.600}',
            700: '{green.700}',
            800: '{green.800}',
            900: '{green.900}',
            950: '{green.950}'
        }
    },
    components: {
        card: {
            colorScheme: {
                dark: {
                    root: {
                        background: 'rgba(26, 26, 26, 0.95)',
                        color: '{surface.0}',
                        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
                        borderRadius: '16px',
                        border: '1px solid rgba(55, 65, 81, 0.3)',
                        backdropFilter: 'blur(20px) saturate(180%)'
                    },
                    body: {
                        padding: '1.5rem'
                    },
                    title: {
                        fontWeight: '600',
                        fontSize: '1.25rem'
                    },
                    subtitle: {
                        color: '{surface.400}'
                    }
                }
            }
        },
        button: {
            colorScheme: {
                dark: {
                    root: {
                        primary: {
                            background: 'linear-gradient(135deg, {primary.600}, {primary.700})',
                            hoverBackground: 'linear-gradient(135deg, {primary.700}, {primary.800})',
                            activeBackground: '{primary.800}',
                            borderColor: '{primary.600}',
                            hoverBorderColor: '{primary.700}',
                            activeBorderColor: '{primary.800}',
                            color: '{primary.contrast.color}',
                            hoverColor: '{primary.contrast.color}',
                            activeColor: '{primary.contrast.color}',
                            focusRing: {
                                color: '{primary.color}',
                                shadow: '0 0 0 2px {surface.950}, 0 0 0 4px {primary.300}, inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                            },
                            boxShadow: '0 4px 14px 0 rgba(34, 197, 94, 0.39)',
                            hoverBoxShadow: '0 6px 20px 0 rgba(34, 197, 94, 0.49)'
                        }
                    }
                }
            }
        },
        inputtext: {
            colorScheme: {
                dark: {
                    root: {
                        background: 'rgba(31, 41, 55, 0.8)',
                        disabledBackground: '{surface.700}',
                        filledBackground: '{surface.800}',
                        filledHoverBackground: '{surface.700}',
                        filledFocusBackground: '{surface.700}',
                        borderColor: 'rgba(55, 65, 81, 0.6)',
                        hoverBorderColor: '{primary.600}',
                        focusBorderColor: '{primary.500}',
                        invalidBorderColor: '{red.400}',
                        color: '{surface.0}',
                        disabledColor: '{surface.500}',
                        placeholderColor: '{surface.400}',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
                        focusBoxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1), 0 0 0 3px rgba(34, 197, 94, 0.15)',
                        invalidBoxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1), 0 0 0 3px {red.300}',
                        borderRadius: '12px',
                        backdropFilter: 'blur(10px)'
                    }
                }
            }
        },
        datatable: {
            colorScheme: {
                dark: {
                    root: {
                        borderColor: 'rgba(55, 65, 81, 0.3)'
                    },
                    header: {
                        background: 'rgba(26, 26, 26, 0.8)',
                        borderColor: 'rgba(55, 65, 81, 0.3)',
                        color: '{surface.0}',
                        backdropFilter: 'blur(10px)'
                    },
                    headerCell: {
                        background: 'transparent',
                        hoverBackground: 'rgba(31, 41, 55, 0.5)',
                        selectedBackground: '{highlight.background}',
                        borderColor: 'rgba(55, 65, 81, 0.3)',
                        color: '{surface.200}',
                        hoverColor: '{surface.0}',
                        selectedColor: '{highlight.color}',
                        gap: '0.5rem',
                        padding: '1rem',
                        focusRing: {
                            width: '1px',
                            style: 'dashed',
                            color: '{primary.500}',
                            offset: '-1px'
                        }
                    },
                    bodyRow: {
                        background: 'rgba(26, 26, 26, 0.4)',
                        hoverBackground: 'rgba(31, 41, 55, 0.6)',
                        selectedBackground: 'rgba(34, 197, 94, 0.1)',
                        color: '{surface.0}',
                        hoverColor: '{surface.0}',
                        selectedColor: '{surface.0}',
                        focusRing: {
                            width: '1px',
                            style: 'dashed',
                            color: '{primary.500}',
                            offset: '-1px'
                        }
                    },
                    bodyCell: {
                        borderColor: 'rgba(55, 65, 81, 0.2)',
                        padding: '1rem'
                    },
                    footerCell: {
                        background: '{surface.800}',
                        borderColor: '{surface.600}',
                        color: '{surface.200}',
                        padding: '1rem'
                    },
                    columnTitle: {
                        fontWeight: '600'
                    },
                    rowToggler: {
                        hoverBackground: '{surface.700}',
                        selectedHoverBackground: '{surface.600}',
                        color: '{surface.400}',
                        hoverColor: '{surface.200}',
                        selectedHoverColor: '{surface.200}',
                        focusRing: {
                            width: '1px',
                            style: 'dashed',
                            color: '{primary.500}',
                            offset: '-1px'
                        }
                    },
                    sort: {
                        icon: {
                            color: '{surface.400}',
                            hoverColor: '{surface.200}'
                        }
                    }
                }
            }
        }
    }
});

export default PremiumPreset;