import { IconButton } from '@material-ui/core';
import GitHubIcon from '@material-ui/icons/GitHub';
import LanguageIcon from '@material-ui/icons/Language';
import ForumIcon from '@material-ui/icons/Forum';

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
        aria-label="Trang web"
        color="inherit"
        href="https://rainbowmusicled.com/"
        target="_blank"
        title="Trang web"
      >
        <LanguageIcon />
      </IconButton>
      <IconButton
        aria-label="Youtube"
        color="inherit"
        href="https://www.youtube.com/channel/UCATBTjpcc1HHLexbgE5ZCdw"
        target="_blank"
        title="Youtube"
      >
        <GitHubIcon />
      </IconButton>
      <IconButton
        aria-label="Fanpage"
        color="inherit"
        href="https://www.facebook.com/rainbowmusicled/"
        target="_blank"
        title="Fanpage"
      >
        <ForumIcon />
      </IconButton>
    </div>
  );
};

export default ButtonBar;
