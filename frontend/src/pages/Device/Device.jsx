import { useEffect } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Grid, Typography } from '@material-ui/core/';
import useStore from '../../utils/apiStore';
import EffectsCard from './Effects';
import PresetsCard from './Presets';
import TransitionCard from './Transition';
import MelbankCard from './Frequencies';
import StreamToCard from './StreamTo';
import { Link } from 'react-router-dom';

const useStyles = makeStyles((theme) => ({
  virtualWrapper: {
    justifyContent: 'center',
  },
  girdItem: { flexShrink: 0, flexGrow: 1, maxWidth: '540px', width: '100%' },
}));

const Device = ({
  match: {
    params: { virtId },
  },
}) => {
  const classes = useStyles();

  const getVirtuals = useStore((state) => state.getVirtuals);
  const getPresets = useStore((state) => state.getPresets);
  const getSchemas = useStore((state) => state.getSchemas);
  const features = useStore((state) => state.features);

  const virtuals = useStore((state) => state.virtuals);
  const presets = useStore((state) => state.presets);

  const getV = () => {
    for (var prop in virtuals) {
      if (virtuals[prop].id == virtId) {
        return virtuals[prop];
      }
    }
  };

  const virtual = getV();
  // Object.keys(virtuals).length && virtuals.find((v) => v.id === virtId);

  const effectType = virtual && virtual.effect.type;

  useEffect(() => {
    getVirtuals();
    getSchemas();
    effectType && getPresets(effectType);
  }, [getVirtuals, getSchemas, getPresets, effectType]);

  // Lắng nghe sự kiện khi hiệu ứng được thay đổi qua systray
  useEffect(() => {
    const handleEffectChangedSystray = (e) => {
      // Cập nhật danh sách thiết bị khi hiệu ứng được thay đổi qua systray
      getVirtuals();

      // Nếu thiết bị hiện tại được thay đổi hiệu ứng, cập nhật presets
      if (
        (e.detail.device_id === virtId || e.detail.device_id === null) &&
        e.detail.effect_type
      ) {
        getPresets(e.detail.effect_type);
      }
    };

    // Lắng nghe sự kiện khi trạng thái đèn LED được thay đổi qua systray
    const handleLedStateChanged = (e) => {
      // Cập nhật danh sách thiết bị khi trạng thái đèn LED được thay đổi
      getVirtuals();
    };

    document.addEventListener('effectChangedSystray', handleEffectChangedSystray);
    document.addEventListener('ledStateChanged', handleLedStateChanged);

    return () => {
      document.removeEventListener('effectChangedSystray', handleEffectChangedSystray);
      document.removeEventListener('ledStateChanged', handleLedStateChanged);
    };
  }, [getVirtuals, getPresets, virtId]);

  return (
    <Grid
      container
      direction="row"
      spacing={2}
      className={classes.virtualWrapper}
    >
      {virtual && (
        <>
          <Grid item className={classes.girdItem}>
            <EffectsCard virtId={virtId} />
          </Grid>

          <Grid item className={classes.girdItem}>
            {effectType && presets && (
              <PresetsCard
                virtual={virtual}
                presets={presets}
                effectType={effectType}
                style={{ marginBottom: '1rem' }}
              />
            )}
            {!(
              features['streamto'] ||
              features['transitions'] ||
              features['frequencies']
            ) && (
              <Typography
                variant={'body2'}
                color={'textSecondary'}
                align={'right'}
              >
                {' '}
                Kích hoạt các tính năng nâng cao hơn với{' '}
                <Link style={{ color: 'inherit' }} to={'/Settings?ui'}>
                  {' '}
                  Chế độ nâng cao
                </Link>
              </Typography>
            )}
            {features['streamto'] && (
              <StreamToCard virtuals={virtuals} virtual={virtual} />
            )}
            {features['transitions'] && (
              <TransitionCard virtual={virtual} style={{ marginTop: '1rem' }} />
            )}
            {features['frequencies'] && (
              <MelbankCard virtual={virtual} style={{ marginTop: '1rem' }} />
            )}
          </Grid>
        </>
      )}
    </Grid>
  );
};

export default Device;
