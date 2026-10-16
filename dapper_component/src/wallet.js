import * as fcl from '@onflow/fcl';
const KEY='mfl_hub_last_wallet';
const address=v=>typeof v==='string'&&/^0x[0-9a-f]{16}$/i.test(v.trim());
let args={},initialized=false,busy=false,storageBlocked=false,forgetting=false;
const connect=document.getElementById('connect'),forget=document.getElementById('forget'),status=document.getElementById('status'),error=document.getElementById('error');
function message(type,extra={}){window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*');}
function emit(action,wallet){message('streamlit:setComponentValue',{value:{action,address:wallet||'',event_id:crypto.randomUUID()},dataType:'json'});}
function read(){try{return localStorage.getItem(KEY);}catch(e){storageBlocked=true;return null;}}
function remember(value){try{if(value)localStorage.setItem(KEY,value);else localStorage.removeItem(KEY);}catch(e){storageBlocked=true;}}
function height(){requestAnimationFrame(()=>message('streamlit:setFrameHeight',{height:document.body.scrollHeight+5}));}
function render(){
 connect.disabled=!args.enabled||busy;
 connect.textContent=busy?'Opening Dapper…':'Connect Dapper';
 forget.hidden=!(args.current_wallet||read());
 status.textContent=storageBlocked?'Browser storage is blocked. Your wallet may need reconnecting next visit.':args.enabled?'Your password stays with Dapper. We use your public wallet address.':'Dapper sign-in is not available yet. Enter your public wallet once below; this browser will remember it.';
 height();
}
window.addEventListener('message',e=>{
 if(e.source!==window.parent||e.data?.type!=='streamlit:render')return;
 args=e.data.args||{};
 if(args.ignore_restore){remember(null);forgetting=false;}
 else if(address(args.current_wallet)&&!forgetting)remember(args.current_wallet.trim().toLowerCase());
 if(!initialized){
  initialized=true;
  const saved=read();
  if(!args.current_wallet&&!args.ignore_restore&&address(saved))emit('restore',saved.trim().toLowerCase());
  const origin=(()=>{try{return new URL(document.referrer).origin;}catch(e){return location.origin;}})();
  fcl.config({'flow.network':'mainnet','accessNode.api':'https://rest-mainnet.onflow.org',
    'discovery.wallet':'https://accounts.meetdapper.com/fcl/authn','discovery.wallet.method':'POP/RPC',
    'app.detail.title':'MFL Management Hub','app.detail.description':'Public MFL agency and player dashboard','app.detail.url':origin});
 }
 render();
});
connect.onclick=async()=>{
 if(!args.enabled||busy)return;
 busy=true;error.textContent='';render();
 try{
  const user=await fcl.authenticate({forceReauth:true});
  if(!user?.loggedIn||!address(user.addr))throw new Error('No wallet selected');
  const wallet=user.addr.toLowerCase();remember(wallet);emit('connected',wallet);
 }catch(e){error.textContent='Dapper connection did not complete. Allow pop-ups and try again, or use your public wallet below.';}
 finally{busy=false;render();}
};
forget.onclick=()=>{forgetting=true;remember(null);fcl.unauthenticate();args.current_wallet='';args.ignore_restore=true;emit('forget');render();};
message('streamlit:componentReady',{apiVersion:1});height();
