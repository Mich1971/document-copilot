import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, Globe, LogOut, MoreVertical, User as UserIcon } from 'lucide-react'

import { supabase } from '@/lib/supabase'
import { useTranslation } from '@/hooks/useTranslation'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuPortal,
    DropdownMenuSeparator,
    DropdownMenuSub,
    DropdownMenuSubContent,
    DropdownMenuSubTrigger,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'

export function UserMenu() {
    const navigate = useNavigate()
    const { t, language, setLanguage } = useTranslation()
    const [email, setEmail] = useState<string>('')

    useEffect(() => {
        supabase.auth.getSession().then(({ data }) => {
            if (data.session?.user?.email) {
                setEmail(data.session.user.email)
            }
        })
    }, [])

    const handleSignOut = async () => {
        await supabase.auth.signOut()
        navigate('/login', { replace: true })
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start gap-2 px-2 hover:bg-muted/50">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <UserIcon className="h-4 w-4" />
                    </div>
                    <div className="flex flex-1 flex-col items-start overflow-hidden text-left">
                        <span className="w-full truncate text-sm font-medium leading-none">{email || 'Usuario'}</span>
                    </div>
                    <MoreVertical className="h-4 w-4 text-muted-foreground" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" side="right" sideOffset={8}>
                <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">Cuenta</p>
                        <p className="text-xs leading-none text-muted-foreground truncate">{email}</p>
                    </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />

                <DropdownMenuSub>
                    <DropdownMenuSubTrigger className="gap-2">
                        <Globe className="h-4 w-4" />
                        <span>Idioma / Language</span>
                    </DropdownMenuSubTrigger>
                    <DropdownMenuPortal>
                        <DropdownMenuSubContent>
                            <DropdownMenuItem onClick={() => setLanguage('es')} className="justify-between">
                                Español {language === 'es' && <Check className="h-4 w-4" />}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => setLanguage('en')} className="justify-between">
                                English {language === 'en' && <Check className="h-4 w-4" />}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => setLanguage('pt')} className="justify-between">
                                Português {language === 'pt' && <Check className="h-4 w-4" />}
                            </DropdownMenuItem>
                        </DropdownMenuSubContent>
                    </DropdownMenuPortal>
                </DropdownMenuSub>

                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut} className="text-destructive focus:text-destructive gap-2">
                    <LogOut className="h-4 w-4" />
                    <span>{t.common.signOut}</span>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}