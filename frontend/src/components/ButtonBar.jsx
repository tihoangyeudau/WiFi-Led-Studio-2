import { IconButton } from '@material-ui/core';
import YouTubeIcon from '@material-ui/icons/YouTube';
import ShoppingCartIcon from '@material-ui/icons/ShoppingCart';
import FacebookIcon from '@material-ui/icons/Facebook';

const ButtonBar = () => {
  return (
    <div
      style={{
        position: 'relative',
        bottom: 0,
        left: 0,
        right: 0,
        paddingTop: '0.4rem',
        paddingBottom: '0.4rem',
        textAlign: 'center',
        color: '#FFFFFF',
        '& > a': {
          margin: '0 5px',
        },
      }}
    >
      <IconButton
        aria-label="Shopee"
        color="inherit"
        href="https://shopee.vn/ambilight.vn"
        target="_blank"
        title="Shopee"
      >
        <ShoppingCartIcon />
      </IconButton>
      <IconButton
        aria-label="Youtube"
        color="inherit"
        href="https://www.youtube.com/channel/UCATBTjpcc1HHLexbgE5ZCdw"
        target="_blank"
        title="Youtube"
      >
        <YouTubeIcon />
      </IconButton>
      <IconButton
        aria-label="Fanpage"
        color="inherit"
        href="https://www.facebook.com/rainbowmusicled/"
        target="_blank"
        title="Fanpage"
      >
        <FacebookIcon />
      </IconButton>
    </div>
  );
};

export default ButtonBar;
