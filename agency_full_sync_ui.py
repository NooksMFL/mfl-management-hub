"""Whole-agency sync control and unfiltered, timestamped analysis export."""
import streamlit as st

import agency_full_sync as full
import wallet_cache_backend as shared


def render(wallet, key):
    if not wallet:
        return
    run = full.state(wallet)
    paused = run.get('status') in ('paused', 'running')
    clicked = st.button('Resume entire agency sync' if paused else 'Sync entire agency',
                        key=key, type='primary', use_container_width=True)
    st.caption('Checks every current agency player: club assignment, age, positions, OVR and attributes. A long sync can be resumed without starting again.')
    if clicked:
        bar = st.progress(0, text='Starting entire agency sync…')
        count = st.empty()

        def progress(done, total, message):
            bar.progress(min(1.0, done / total) if total else 0, text=message)
            count.caption(f'{done} / {total} player profiles checked' if total else f'{done} player IDs found so far')

        try:
            result = full.sync(wallet, progress=progress)
        except Exception:
            bar.empty()
            st.error('The sync could not finish. Previously completed data is retained. Use Resume entire agency sync to retry.')
        else:
            bar.empty()
            count.empty()
            if result.get('busy'):
                st.warning('This wallet already has a sync running. Wait for it to finish; if interrupted, you can resume after two minutes.')
            else:
                st.rerun()
    run = full.state(wallet)
    if run.get('status') == 'complete':
        st.success(f"Entire agency synced: {run['checked']} / {len(run['ids'])} profiles checked · {len(run['clubs'])} owned clubs · {run['completed_at']}")
        if run.get('unverified_clubs') or run.get('missing_squad_fields'):
            st.warning(f"MFL did not supply a verifiable current club for {run.get('unverified_clubs',0)} player(s); {run.get('missing_squad_fields',0)} have missing position/OVR data. These fields are marked in the export.")
    elif run.get('status') == 'paused':
        st.warning(f"Entire agency sync incomplete: {run.get('checked',0)} / {len(run.get('ids') or [])} profiles checked. The previous completed snapshot is still in use.")
        st.caption(run.get('error') or 'Resume to finish checking the remaining players.')
    elif run.get('status') == 'running':
        st.info(f"Entire agency sync is running or was interrupted: {run.get('checked',0)} profiles saved so far.")
    completed = shared._meta_get(wallet, 'agency_full_sync_completed_at')
    if completed:
        export = full.export_frame(wallet)
        # An authoritative empty agency is still a completed sync.
        data = export.to_csv(index=False).encode('utf-8-sig') if not export.empty else b'Player ID,Player,Club,Profile checked (UTC),Full sync completed (UTC)\n'
        st.download_button(f'Download full agency CSV ({len(export)})', data,
                           file_name=f'mfl_full_agency_{wallet}_{completed[:10]}.csv', mime='text/csv', key=key+'_csv')
        st.caption(f'Last completed snapshot: {completed}. Includes every synced player, even those without a club; it does not use the retired-player display filter. Players loaned in from another owner are outside an agency-wallet export.')
