import { Card, CardContent } from '@material-ui/core';
import { ComponentStory, ComponentMeta } from '@storybook/react';
// eslint-disable-next-line
import DropDown from "./DropDown";

export default {
  /* 👇 The title prop is optional.
   * See https://storybook.js.org/docs/react/configure/overview#configure-story-loading
   * to learn how to generate automatic titles
   */
  title: 'UI Components/SchemaForm/Examples',
  component: DropDown,
  argTypes: {
    type: {
      control: false,
    },
  },
  decorators: [
    (Story) => (
      <Card style={{ maxWidth: 800 }}>
        <CardContent>{Story()}</CardContent>
      </Card>
    ),
  ],
  parameters: {
    options: {
      showPanel: true,
      panelPosition: 'bottom',
    },
  },
} as ComponentMeta<typeof DropDown>;

// eslint-disable-next-line
const Template: ComponentStory<typeof DropDown> = (args) => <DropDown {...args} />;

export const EffectType = Template.bind({});
EffectType.storyName = 'Effect Type';
EffectType.args = {
  showFilter: false,
  groups: {
    'Không nháy theo nhạc': [
      {
        name: 'Dải mầu',
        id: 'gradient',
        category: 'Không nháy theo nhạc',
      },
      {
        name: 'Phai mầu',
        id: 'fade',
        category: 'Không nháy theo nhạc',
      },
      {
        name: 'Cầu vồng',
        id: 'rainbow',
        category: 'Không nháy theo nhạc',
      },
      {
        name: 'Mầu đơn',
        id: 'singleColor',
        category: 'Không nháy theo nhạc',
      },
    ],
    '2D': [
      {
        name: 'Băng tần',
        id: 'bands',
        category: '2D',
      },
      {
        name: 'Ma trận Băng tần',
        id: 'bands_matrix',
        category: '2D',
      },
      {
        name: 'Khối',
        id: 'blocks',
        category: '2D',
      },
      {
        name: 'Bộ chỉnh âm',
        id: 'equalizer',
        category: '2D',
      },
    ],
    'BPM': [
      {
        name: 'Thanh',
        id: 'bar',
        category: 'BPM',
      },
      {
        name: 'Thanh mầu',
        id: 'multiBar',
        category: 'BPM',
      },
      {
        name: 'Nhấp nháy',
        id: 'strobe',
        category: 'BPM',
      },
    ],
    'Cổ điển': [
      {
        name: 'RML pro',
        id: 'blade_power_plus',
        category: 'Cổ điển',
      },
      {
        name: 'Năng lượng',
        id: 'energy',
        category: 'Cổ điển',
      },
      {
        name: 'Độ lớn',
        id: 'magnitude',
        category: 'Cổ điển',
      },
      {
        name: '',
        id: 'Tần số quang phổ',
        category: 'Cổ điển',
      },
      {
        name: 'Sức mạnh',
        id: 'power',
        category: 'Cổ điển',
      },
      {
        name: 'Mưa',
        id: 'rain',
        category: 'Cổ điển',
      },
      {
        name: 'Nháy cực đỉnh',
        id: 'real_strobe',
        category: 'Cổ điển',
      },
      {
        name: 'Cuộn',
        id: 'scroll',
        category: 'Cổ điển',
      },
      {
        name: 'Quang phổ',
        id: 'spectrum',
        category: 'Cổ điển',
      },
      {
        name: 'Bước sóng',
        id: 'wavelength',
        category: 'Cổ điển',
      },
    ],
    'Dạng áp suất': [
      {
        name: 'Chặn phản xạ',
        id: 'block_reflections',
        category: 'Dạng áp suất',
      },
      {
        name: 'Crawler',
        id: 'crawler',
        category: 'Dạng áp suất',
      },
      {
        name: 'Energy 2',
        id: 'energy2',
        category: 'Dạng áp suất',
      },
      {
        name: 'Fire',
        id: 'fire',
        category: 'Dạng áp suất',
      },
      {
        name: 'Nhiễu sọc',
        id: 'glitch',
        category: 'Dạng áp suất',
      },
      {
        name: 'Đèn lava',
        id: 'lava_lamp',
        category: 'Dạng áp suất',
      },
      {
        name: 'Diễu hành',
        id: 'marching',
        category: 'Dạng áp suất',
      },
      {
        name: 'Tan chẩy',
        id: 'melt',
        category: 'Dạng áp suất',
      },
    ],
  },
  value: '',
  onChange: undefined,
};
