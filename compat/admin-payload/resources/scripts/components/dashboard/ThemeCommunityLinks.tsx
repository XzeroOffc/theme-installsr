import React from 'react';

interface CommunityLink {
    label: string;
    description: string;
    url: string;
    enabled: boolean;
}
interface CommunitySettings {
    theme: string;
    heading: string;
    enabled: boolean;
    owner: boolean;
    links: Record<string, CommunityLink>;
}
declare global {
    interface Window {
        ThemeInstallerSettings?: CommunitySettings;
    }
}

export default function ThemeCommunityLinks() {
    const settings = window.ThemeInstallerSettings;
    if (!settings?.enabled) return null;
    const keys = ['admin', 'channel', 'group'];
    const links = keys.filter((key) => {
        const link = settings.links[key];
        return link?.enabled && /^https?:\/\//i.test(link.url);
    });
    if (!links.length) {
        return settings.owner ? (
            <p className="ti-community-empty">
                Tautan komunitas belum diisi. <a href="/admin/theme-installsr">Atur Chat Admin, Channel, dan Group</a>.
            </p>
        ) : null;
    }
    const images: Record<string, string> = { admin: 'contact', channel: 'channel', group: 'group' };
    return (
        <section className="ti-community" aria-labelledby="ti-community-heading">
            <h2 id="ti-community-heading">{settings.heading}</h2>
            <div className="ti-community-grid">
                {links.map((key) => {
                    const link = settings.links[key];
                    return (
                        <article className="ti-community-card" key={key}>
                            {settings.theme === 'enigma' && (
                                <img src={`/themes/enigma_premium/img/${images[key]}_logo.png`} alt="" width={64} height={64} />
                            )}
                            <h3>{link.label}</h3>
                            {link.description && <p>{link.description}</p>}
                            <a href={link.url} target="_blank" rel="noopener noreferrer" aria-label={`${key === 'admin' ? 'Chat' : 'Gabung'} ${link.label} (tab baru)`}>
                                {key === 'admin' ? 'Chat' : 'Gabung'}
                            </a>
                        </article>
                    );
                })}
            </div>
        </section>
    );
}
