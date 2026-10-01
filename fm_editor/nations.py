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

# Added from the 5 biggest clubs per id (same method; local club names identify the nation).
NATION_NAMES.update({
    0: 'Algeria', 1: 'Angola', 2: 'Benin', 3: 'Botswana', 4: 'Burkina Faso', 5: 'Burundi',
    6: 'Cameroon', 7: 'Cape Verde', 8: 'Central African Republic', 9: 'Chad', 10: 'Djibouti',
    12: 'Equatorial Guinea', 13: 'Ethiopia', 14: 'Gabon', 15: 'Gambia', 16: 'Ghana', 17: 'Guinea',
    18: 'Guinea-Bissau', 19: 'Ivory Coast', 20: 'Kenya', 21: 'Lesotho', 22: 'Liberia',
    23: 'Libya', 24: 'Madagascar', 25: 'Malawi', 26: 'Mali', 27: 'Mauritania', 28: 'Mauritius',
    30: 'Mozambique', 31: 'Namibia', 32: 'Niger', 34: 'Rwanda', 35: 'Sao Tome and Principe',
    36: 'Senegal', 38: 'Sierra Leone', 39: 'Somalia', 40: 'South Africa', 41: 'Sudan',
    42: 'Eswatini', 43: 'Tanzania', 44: 'Congo', 45: 'Togo', 46: 'Tunisia', 47: 'Uganda',
    48: 'DR Congo', 49: 'Zambia', 50: 'Zimbabwe', 51: 'Afghanistan', 52: 'Bahrain', 54: 'Brunei',
    55: 'China', 56: 'Hong Kong', 57: 'India', 58: 'Indonesia', 59: 'Iran', 60: 'Iraq',
    62: 'Jordan', 63: 'Cambodia', 65: 'Kuwait', 66: 'Kyrgyzstan', 67: 'Laos', 68: 'Lebanon',
    69: 'Macau', 70: 'Malaysia', 71: 'Maldives', 73: 'Nepal', 74: 'North Korea', 75: 'Oman',
    76: 'Pakistan', 79: 'Singapore', 81: 'Sri Lanka', 82: 'Syria', 83: 'Taiwan', 84: 'Tajikistan',
    85: 'Thailand', 86: 'Philippines', 87: 'Turkmenistan', 89: 'Uzbekistan', 90: 'Vietnam',
    91: 'Yemen', 92: 'Antigua and Barbuda', 93: 'Aruba', 94: 'Barbados', 95: 'Belize',
    96: 'Bermuda', 98: 'Cayman Islands', 100: 'Cuba', 105: 'Guyana', 106: 'Haiti', 110: 'Curacao',
    113: 'Puerto Rico', 116: 'St Vincent and the Grenadines', 117: 'Suriname', 118: 'Bahamas',
    127: 'Andorra', 151: 'Latvia', 154: 'Luxembourg', 156: 'Malta', 166: 'San Marino',
    178: 'Cook Islands', 179: 'Fiji', 180: 'New Zealand', 181: 'Papua New Guinea',
    182: 'Solomon Islands', 183: 'Tahiti', 184: 'Tonga', 185: 'Vanuatu', 186: 'Samoa',
    197: 'Palestine', 202: 'Mongolia', 204: 'Eritrea', 206: 'British Virgin Islands',
    207: 'Montserrat', 208: 'US Virgin Islands', 209: 'Turks and Caicos', 211: 'Bhutan',
    212: 'Dominican Republic', 215: 'Kiribati', 234: 'Comoros', 236: 'Timor-Leste',
    240: 'South Sudan',
    205: 'Anguilla', 225: 'French Guiana', 226: 'Guadeloupe', 227: 'Martinique', 230: 'Reunion',
    231: 'Mayotte',
})


def nation_name(nation_id):
    return NATION_NAMES.get(nation_id)


STATUS_NAMES = {1: 'Professional', 2: 'Semi-professional', 3: 'Amateur'}
