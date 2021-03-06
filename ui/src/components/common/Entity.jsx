import React, { Component } from 'react';
import { FormattedMessage } from 'react-intl';
import { Link } from 'react-router-dom';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import truncateText from 'truncate';
import c from 'classnames';

import { Schema } from 'src/components/common';
import togglePreview from 'src/util/togglePreview';
import { fetchEntity as fetchEntityAction } from 'src/actions';
import { selectEntity } from 'src/selectors';
import getEntityLink from 'src/util/getEntityLink';

import './Entity.scss';


class EntityLabel extends Component {
  shouldComponentUpdate(nextProps) {
    const { entity = {} } = this.props;
    const { entity: nextEntity = {} } = nextProps;
    return entity.id !== nextEntity.id;
  }

  render() {
    const {
      entity, icon = false, documentMode = false, truncate,
    } = this.props;

    if (!entity) {
      return null;
    }
    const title = entity.getFirst('title') || entity.getCaption();
    const fileName = entity.getFirst('fileName') || title;
    const caption = title || fileName;
    const fullLabel = documentMode ? fileName : caption;
    const label = truncate ? truncateText(fullLabel, truncate) : fullLabel;
    return (
      <span className={c('EntityLabel', { untitled: !label })} title={caption}>
        {icon && <Schema.Icon schema={entity.schema} />}
        { !label && (
          <FormattedMessage id="entity.label.missing" defaultMessage="Untitled" />
        )}
        {label}
      </span>
    );
  }
}


class EntityLink extends Component {
  constructor(props) {
    super(props);
    this.onClick = this.onClick.bind(this);
  }

  onClick(event) {
    const { entity, history, preview } = this.props;
    if (preview) {
      event.preventDefault();
      togglePreview(history, entity, 'entity');
    }
  }

  render() {
    const { entity, className } = this.props;
    if (!entity || !entity.schema) {
      return <Entity.Label {...this.props} />;
    }
    return (
      <Link to={getEntityLink(entity)} onClick={this.onClick} className={c('EntityLink', className)}>
        <Entity.Label {...this.props} />
      </Link>
    );
  }
}


class EntityLoad extends Component {
  componentDidMount() {
    this.fetchIfNeeded();
  }

  componentDidUpdate() {
    this.fetchIfNeeded();
  }

  fetchIfNeeded() {
    const { id, entity, fetchEntity } = this.props;
    if (entity.shouldLoad) {
      fetchEntity({ id });
    }
  }

  render() {
    const { entity, children, renderWhenLoading } = this.props;
    if (entity.isLoading && renderWhenLoading !== undefined) {
      return renderWhenLoading;
    }
    return children(entity);
  }
}

const mapStateToProps = (state, ownProps) => ({
  entity: selectEntity(state, ownProps.id),
});

class Entity {
  static Label = EntityLabel;

  static Link = withRouter(EntityLink);

  static Load = connect(mapStateToProps, { fetchEntity: fetchEntityAction })(EntityLoad);
}

export default Entity;
