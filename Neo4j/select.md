## Vyhledejte prvních 10 uživatelů v databázi

MATCH (u:User)
RETURN u
LIMIT 3;

## Najděte všechny uživatele, kteří žijí v nějakém zadaném městě



## Vytvořte vztah, kde "Alice" sleduje "Boba"
## Zobrazte 5 uživatelů s největším počtem příspěvku
## Zobrazte prvních 10 vztahů, kde jeden uživatel sleduje jiného
## Zobrazte 10 příspěveků a jejich komentáře
## Odstraňte vztah, kde "Alice" sleduje "Boba"
## Najděte 5 uživatelů s největším počtem sledujících
## Najděte uživatele, kteří komentovali příspěvek jiného uživatele, a zobrazte obsah příspěvku

MATCH (u:User) - [r:COMMENTED|FOLLOWS|CREATED] -> ()
RETURN u, count(r) as a_n
ORDER BY a_n DESC