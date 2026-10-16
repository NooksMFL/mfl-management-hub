"""Teletext agency and individual-player valuation interface."""
import pandas as pd
import streamlit as st
import agency_backend as agency
import wallet_cache_backend as shared
import valuation_backend as valuation


def roster(wallet):
    rows=shared.roster_rows(wallet)
    if rows:
        return [{'player_id':r['player_id'],'player':r['player_name'],'age':r['age'],'position':r['position'],
                 'current_ovr':r['overall'],'club':r['club']} for r in rows], 'shared wallet roster'
    c=agency.db();agency.init(c);agency.ensure_v2(c)
    try:
        rows=c.execute('''SELECT o.player_id,o.player_name player,o.current_ovr,m.age,m.position,m.club
                         FROM ownership_v65 o LEFT JOIN player_meta m
                         ON m.wallet=o.wallet AND m.player_id=o.player_id WHERE o.wallet=?''',(wallet.lower(),)).fetchall()
    finally:
        c.close()
    return [dict(r) for r in rows], 'saved agency analysis (may include older ownership data)'


def render(wallet):
    st.title('Agency / Player Valuation')
    st.write('Estimate your agency and individual players from comparable active MFL asking prices.')
    st.caption('These are indicative listing-based estimates, not completed-sale values or guaranteed proceeds. Player attributes, traits and market liquidity are not modelled.')
    if not wallet:
        st.info('Connect a wallet in the sidebar to value your agency.')
        return
    records,source=roster(wallet)
    if not records:
        st.info('Load your shared wallet roster in page 888 Sync Centre, then return here.')
        return
    st.caption(f'{len(records)} players loaded from {source}. Refresh your wallet in Sync Centre after transfers or development.')
    depth=st.selectbox('Market scan depth',['Quick · up to 150 listings','Standard · up to 300 listings','Deep · up to 600 listings'],index=1)
    snapshot=valuation.load_market()
    if st.button('Refresh market and value agency',type='primary',key='valuation_refresh'):
        progress=st.empty()
        try:
            with st.spinner('Reading active player listings…'):
                snapshot=valuation.fetch_market([6,12,24][['Quick · up to 150 listings','Standard · up to 300 listings','Deep · up to 600 listings'].index(depth)],
                    lambda page,total,count:progress.caption(f'Market page {page}/{total} · {count} records scanned'))
            progress.success('Market snapshot saved. Agency values updated.')
        except RuntimeError as exc:
            progress.empty();st.error(str(exc))
    if not snapshot:
        st.info('Refresh the market to calculate estimates. No prices are invented for players without market evidence.')
        return
    captured=pd.to_datetime(snapshot['captured_at'],utc=True).tz_convert('Europe/London').strftime('%d %b %Y %H:%M %Z')
    st.caption(f"Market snapshot: {captured} · {len(snapshot['listings'])} usable listings from {snapshot['records_scanned']} scanned records. This is a sampled market, not the entire marketplace.")
    currencies=sorted({p['currency'] for p in snapshot['listings']})
    currency=st.selectbox('Price currency / unit',currencies)
    if currency=='MARKET UNITS':
        st.warning('MFL did not identify the currency in these listings. Values are shown in raw market price units; no USD label or conversion is assumed.')
    output,evidence=valuation.value_agency(records,snapshot['listings'],currency)
    frame=pd.DataFrame(output)
    active=frame[frame.Status!='Retired / no current club']
    priced=active[active.Estimate.notna()]
    missing=len(active)-len(priced)
    a,b,c=st.columns(3)
    a.metric('Agency estimate' if not missing else 'Priced-player subtotal',f"{priced.Estimate.sum():,.2f}" if not priced.empty else '—')
    b.metric('Valuation coverage',f'{len(priced)}/{len(active)} active players')
    c.metric('Players without an estimate',missing)
    if not priced.empty:
        st.write(f"{currency} · Combined comparable asking range: {priced['Lower ask'].sum():,.2f}–{priced['Upper ask'].sum():,.2f}.")
        st.caption('Range sums each player’s 25th–75th percentile comparable asking prices. It is not a confidence interval, agency sale offer or expected liquidation value.')
    if missing:
        st.warning(f'{missing} active players have no supported estimate. The subtotal is not the value of the entire agency.')
    st.caption(f"{len(frame)-len(active)} retired / no-club players excluded from valuation. Your own agency’s listings are excluded from the reference pool.")
    st.subheader('Every player')
    a,b=st.columns([2,1])
    query=a.text_input('Search player or club',key='valuation_search')
    status=b.selectbox('Valuation filter',['All players','Estimated','Unpriced active','Retired / no club'])
    view=frame.copy()
    if query:
        view=view[view.Player.fillna('').str.contains(query,case=False,regex=False)|view['Current club'].fillna('').str.contains(query,case=False,regex=False)]
    if status=='Estimated':view=view[view.Estimate.notna()]
    elif status=='Unpriced active':view=view[(view.Estimate.isna())&(view.Status!='Retired / no current club')]
    elif status=='Retired / no club':view=view[view.Status=='Retired / no current club']
    st.dataframe(view.sort_values('Estimate',ascending=False,na_position='last'),hide_index=True,use_container_width=True)
    export=frame.assign(**{'Market snapshot':snapshot['captured_at']})
    st.download_button('Download agency valuations CSV',export.to_csv(index=False).encode('utf-8-sig'),
                       file_name='mfl_agency_valuations.csv',mime='text/csv')
    st.subheader('Individual player / valuation evidence')
    options={f"{r['Player']} · {r['Player ID']}":r for r in output}
    selected=options[st.selectbox('Player to inspect',list(options),key='valuation_player')]
    st.write(f"{selected['Player']} · {selected['Positions']} · Age {selected['Age']} · OVR {selected['OVR']}")
    if selected['Estimate'] is None:
        st.info(selected['Status']+'. No supported price is available from this market snapshot.')
    else:
        st.metric('Player estimate',f"{selected['Estimate']:,.2f} {currency}")
        st.write(f"{selected['Match']} match · {selected['Comparables']} independent comparables · asking range {selected['Lower ask']:,.2f}–{selected['Upper ask']:,.2f}.")
        st.dataframe(pd.DataFrame(evidence[selected['Player ID']]),hide_index=True,use_container_width=True)
    with st.expander('How values are calculated'):
        st.write('Median of at least five different listed players sharing a recognised position, within ±3 OVR and ±3 years. If that is unavailable, a clearly marked broader ±5 OVR / ±5-year sample is tried. Each player is counted once; your own agency listings and other currencies are excluded. Retired players and unsupported comparisons stay unpriced. No age multiplier, assumed price floor or invented fallback price is used.')
