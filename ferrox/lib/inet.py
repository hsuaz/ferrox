
import re

IPV4PREFIX = "\0\0\0\0\0\0\0\0\0\0\xff\xff"

def pton(value):
    types = [
        '^[0-9]+(\.[0-9]+){3}$',
        '^((:|(0+:)+)0?(:0+)*):ffff:([0-9]+(\.[0-9]+){3})$',
        '^(:|(0*[a-f0-9]{,4}:)+)(:|(0*[a-f0-9]{,4})?(:0*[a-f0-9]{,4})+)$'
    ]

    for i in range(0,len(types)):
        match = re.match(types[i],value,re.IGNORECASE)
        if (match): break

    if not match:
        raise Exception('Invalid IP('+value+').')

    out = ''

    if (i == 0):
        match = match.group(0)
    elif (i == 1):
        if len(match.group(1).split(':') ) > 5: raise Exception('Invalid IP('+value+').')
        match = match.group(5)
    else:
        match = match.group(0)

        # Original: tirando dois pontos duplos no inicio ou fim para gerar um array
        # Loosely translated: Removing colon from beginning or end to generate an array
        if match[0] == ':':
            match = match[1:];
        if match[-1] == ':':
            match = match[:-1]

        match = match.split(':');

        l = len(match);
        if l > 8: raise Exception('Invalid IP('+value+').')
        octs = l

        for i in range(0,l):
            p = match[i]
            lp = len(p);
            if lp == 0: #p vazio, preencha com os octetos restantes 
                # (p empty, fill remaining octets)
                for j in range(octs-1,8):    out += "\0\0"
                octs = 8
            elif lp < 4: #p menor que 4, preencha com zeros 
                # (p less than 4, fill with zeros) 
                for j in range(lp,4): p = '0' + p
            elif lp > 4: #p menor que 4, remova os zeros extras 
                # (p greater than 4, remove extra zeros)
                p = p[-4:]

            if p:
                p = [p[:2],p[2:] ];
                for i in range (0,2):
                    c = int(p[i],16);
                    out += chr(c);

        #falhar so nao houverem exatamente 8 octetos 
        # (make sure there are exactly eight octets)
        if octs != 8: raise Exception('Invalid IP('+value+').')

        return out

    match = match.split('.');
    for x in range(0, 4):
        match[x] = int( match[x] );
        if match[x] > 255: raise Exception('Invalid IP('+value+').')
        c = chr(match[x])
        out += c;

    return IPV4PREFIX + out;

def ntop(value):
    out = ''
    value = str(value)

    for i in range(0,16):
        c = value[i]
        n = ord(c)
        c = "%X" % n
        if (n < 16): c = '0'+c
        out += c
        if (i % 2 == 1 and i != 15): out += ':'

    if value.startswith(IPV4PREFIX):
        out += ' (';
        for i in range (12,16):
            out += str (ord(value[i]) )
            if i != 15: out += '.'
        out += ')'
    return out
