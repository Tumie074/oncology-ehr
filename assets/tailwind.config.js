// Design tokens copied from the CHRS tailwind.config.js. Rebuild with:
//   npx tailwindcss@3 -c assets/tailwind.config.js -i assets/input.css -o static/css/chrs.css --minify
module.exports = {
  content: ['./templates/**/*.html', './*/templates/**/*.html'],
  theme: { extend: {
    colors: {
      paper:'#F6F2FA', ink:'#1C1B1A',
      clinical:{50:'#F3EEF8',100:'#DCCFEA',400:'#8E5FC4',500:'#5B2A86',600:'#3E1B5E',700:'#2E1448'},
      alert:{50:'#FBEAE9',100:'#F5CFCC',500:'#B3261E',600:'#8C1D17'},
      amber:{50:'#FDF3E0',100:'#FAE3B8',500:'#B87503',600:'#8F5A02'},
      confirm:{50:'#E8F5EC',500:'#2E7D4F',600:'#1F5C38'},
      slate:{50:'#F6F2FA',100:'#E9E1F2',200:'#D9CCE8',300:'#C4B3D8',500:'#7B6A8F',700:'#4A3B5C'},
      footprints:{50:'#F3EEF8',100:'#DCCFEA',400:'#8E5FC4',600:'#5B2A86',700:'#3E1B5E'},
      lime:{50:'#F2FCDC',400:'#A3E635',600:'#4D7C0F'}
    },
    fontFamily:{ sans:['"Work Sans"','system-ui','sans-serif'], mono:['"IBM Plex Mono"','ui-monospace','monospace'] },
    borderRadius:{ DEFAULT:'6px' },
    boxShadow:{ card:'0 1px 2px rgba(28,27,26,.06), 0 1px 3px rgba(28,27,26,.08)' }
  } },
  plugins: [],
}
