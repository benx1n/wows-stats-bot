Move-Item .\hoshino\config_example .\hoshino\config
Remove-Item .\hoshino\config\__bot__.py
Remove-Item .\hoshino\config\__init__.py
Move-Item .\hoshino\modules\wows-stats-bot\ci\init.py .\hoshino\config\__init__.py

Get-ChildItem '.\hoshino\modules\*' | Where-Object -Property name -NotMatch "wows.*bot|groupmaster|botmanage" | ForEach-Object {
    Remove-Item -Recurse -Force $_
}

Get-ChildItem '.\hoshino\modules\wows-stats-bot\*.py' | ForEach-Object {
    (Get-Content $_ -Encoding UTF8) -replace "cfgpath.*'config.json'.*","cfgpath='wwsbotconfig.json'" | Set-Content $_ -Encoding UTF8
}

Remove-Item -Recurse -Force '.\hoshino\modules\wows-stats-bot\.git'
Remove-Item -Recurse -Force '.\hoshino\modules\wows-stats-bot\.github'
Move-Item '.\hoshino\modules\wows-stats-bot\ci' .

$env:PLAYWRIGHT_BROWSERS_PATH="0"
playwright install chromium
pyinstaller -F run.py `
    --add-data "hoshino;hoshino" `
    --hidden-import "aiohttp" `
    --hidden-import "markdown" `
    --hidden-import "playwright" `
    --collect-all "playwright" `
    --hidden-import "sqlite3" `
    --collect-all "sqlite3" `
    --hidden-import "requests" `
    --collect-all "requests" `
    --hidden-import "bs4" `
    --collect-all "bs4" `
    --collect-all "nonebot" `
    --collect-all "zhconv" --noupx

Move-Item dist\run.exe ci\hikari.exe
Compress-Archive -DestinationPath release.zip `
    -LiteralPath 'ci\hikari.exe','ci\hoshino_config.py','ci\wwsbotconfig.json','ci\readme.txt'