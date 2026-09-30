"""Nation entity id -> name for the ids seen on club records (club record +13, person end+9).

The save stores no nation-name table (names come from the install language files), so this is a
hand table. Every id here was verified by reading the 4+ biggest clubs carrying that id in the
2026-27 Spurs save (e.g. 131 = Club Brugge, Genk, Union SG, Standard ...). Unknown ids -> None.
"""
NATION_NAMES = {
    64: 'Kazakhstan', 77: 'Qatar', 78: 'Saudi Arabia', 88: 'United Arab Emirates',
    99: 'Costa Rica', 102: 'El Salvador', 104: 'Guatemala', 107: 'Honduras',
    108: 'Jamaica', 109: 'Mexico', 111: 'Nicaragua', 112: 'Panama',
    119: 'Trinidad and Tobago', 120: 'United States', 126: 'Albania', 128: 'Armenia',
    129: 'Austria', 130: 'Azerbaijan', 131: 'Belgium', 132: 'Belarus',
    133: 'Bosnia and Herzegovina', 134: 'Bulgaria', 135: 'Croatia', 136: 'Cyprus',
    137: 'Czech Republic', 138: 'Denmark', 139: 'England', 140: 'Estonia',
    141: 'Faroe Islands', 142: 'Finland', 143: 'France', 144: 'Georgia', 145: 'Germany',
    146: 'Greece', 147: 'Hungary', 148: 'Iceland', 149: 'Israel', 150: 'Italy',
    153: 'Lithuania', 155: 'North Macedonia', 157: 'Moldova', 158: 'Netherlands',
    159: 'Northern Ireland', 160: 'Norway', 161: 'Poland', 162: 'Portugal',
    163: 'Republic of Ireland', 164: 'Romania', 165: 'Russia', 167: 'Scotland',
    168: 'Slovakia', 169: 'Slovenia', 170: 'Spain', 171: 'Sweden', 172: 'Switzerland',
    173: 'Turkey', 174: 'Ukraine', 176: 'Serbia', 187: 'Argentina', 188: 'Bolivia',
    189: 'Brazil', 190: 'Chile', 191: 'Colombia', 192: 'Ecuador', 193: 'Paraguay',
    194: 'Peru', 195: 'Uruguay', 196: 'Venezuela', 216: 'Gibraltar', 219: 'Kosovo',
    247: 'Montenegro',
}


def nation_name(nation_id):
    return NATION_NAMES.get(nation_id)


STATUS_NAMES = {1: 'Professional', 2: 'Semi-professional', 3: 'Amateur'}
