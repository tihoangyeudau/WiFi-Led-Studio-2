import { ComponentStory, ComponentMeta } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';

// eslint-disable-next-line
import DeviceCard from './DeviceCard';

export default {
  /* 👇 The title prop is optional.
   * See https://storybook.js.org/docs/react/configure/overview#configure-story-loading
   * to learn how to generate automatic titles
   */
  title: 'UI Components/DeviceCard',
  component: DeviceCard,
  decorators: [(Story) => <MemoryRouter>{Story()}</MemoryRouter>],
  parameters: {
    options: {
      showPanel: true,
    },
  },
} as ComponentMeta<typeof DeviceCard>;

// eslint-disable-next-line
const Template: ComponentStory<typeof DeviceCard> = (args) => (
  <DeviceCard {...args} />
);

export const Default = Template.bind({});
Default.args = {
  deviceName: 'Đèn của tôi',
  iconName: 'rml',
  effectName: 'Super Effect',
  isEffectSet: true,
  isPlaying: true,
  previewOnly: true,
  colorIndicator: true,
  isStreaming: false,
  graphsActive: true,
  handleDeleteDevice: undefined,
  handleEditVirtual: undefined,
  handleClearEffect: undefined,
  handlePlayPause: undefined,
  additionalStyle: {},
  transitionTime: 5,
  virtId: 'yz-quad',
  isDevice: 'yz-quad',
  linkTo: '/',
  index: 1,
};
